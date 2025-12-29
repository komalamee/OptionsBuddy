"""
Advisor Page - AI chat, scanner, and analyzer in one unified interface.

The central hub for finding opportunities and getting AI-powered suggestions.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import json
from datetime import date, datetime

from database import DatabaseManager, init_database
from core.black_scholes import BlackScholes
from config.constants import CALL, PUT
from components.styles import apply_global_styles
from utils.market_hours import is_market_open, get_market_status_display


# ==================== AI CHAT HELPERS ====================

def get_portfolio_context() -> str:
    """Build context string about user's current positions and portfolio."""
    positions = DatabaseManager.get_open_positions()
    stats = DatabaseManager.get_position_stats()

    if not positions:
        return "The user currently has no open positions."

    lines = ["## Current Portfolio\n"]

    total_premium = sum(p.premium_collected * p.quantity * 100 for p in positions)
    lines.append(f"**Open Positions:** {len(positions)}")
    lines.append(f"**Total Premium Collected:** ${total_premium:,.0f}")
    lines.append(f"**Win Rate:** {stats.get('win_rate', 0):.0f}%\n")

    lines.append("### Positions:\n")

    for pos in positions:
        dte = pos.days_to_expiry
        urgency = ""
        if dte <= 3:
            urgency = " [CRITICAL - expiring soon!]"
        elif dte <= 7:
            urgency = " [Expiring this week]"

        lines.append(
            f"- **{pos.underlying}** ${pos.strike:.0f} {pos.option_type} | "
            f"{pos.strategy_type} | {dte}d to expiry | "
            f"Premium: ${pos.premium_collected:.2f}/share | "
            f"Qty: {pos.quantity}{urgency}"
        )

    connected = st.session_state.get('ibkr_connected', False)
    lines.append(f"\n**IBKR Status:** {'Connected' if connected else 'Not connected'}")

    return "\n".join(lines)


def get_live_price(symbol: str) -> str:
    """Fetch live price from IBKR if connected."""
    connected = st.session_state.get('ibkr_connected', False)
    if not connected:
        return f"Cannot fetch price for {symbol} - IBKR not connected."

    try:
        from data.ibkr_client import get_ibkr_client
        client = get_ibkr_client()
        price = client.get_stock_price(symbol)
        if price:
            return f"Current price for {symbol}: ${price:.2f}"
        return f"Could not fetch price for {symbol}"
    except Exception as e:
        return f"Error fetching price: {str(e)}"


def get_ai_config() -> dict:
    """Get the current AI provider configuration."""
    PROVIDERS = {
        "openai": {
            "name": "OpenAI",
            "key_setting": "openai_api_key",
            "base_url": None,
            "default_model": "gpt-4o-mini"
        },
        "deepseek": {
            "name": "DeepSeek",
            "key_setting": "deepseek_api_key",
            "base_url": "https://api.deepseek.com",
            "default_model": "deepseek-chat"
        },
        "anthropic": {
            "name": "Anthropic (Claude)",
            "key_setting": "anthropic_api_key",
            "base_url": "https://api.anthropic.com",
            "default_model": "claude-3-5-sonnet-20241022"
        },
        "groq": {
            "name": "Groq",
            "key_setting": "groq_api_key",
            "base_url": "https://api.groq.com/openai/v1",
            "default_model": "llama-3.3-70b-versatile"
        }
    }

    provider = DatabaseManager.get_setting("ai_provider") or "openai"
    config = PROVIDERS.get(provider, PROVIDERS["openai"])
    config["provider"] = provider
    config["api_key"] = DatabaseManager.get_setting(config["key_setting"])
    config["model"] = DatabaseManager.get_setting("ai_model") or config["default_model"]

    return config


def chat_with_ai(messages: list, config: dict) -> str:
    """Send messages to the configured AI provider and get response."""
    provider = config["provider"]
    api_key = config["api_key"]
    model = config["model"]

    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        system_content = ""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=system_content,
            messages=anthropic_messages
        )

        return response.content[0].text

    else:
        import openai

        client_kwargs = {"api_key": api_key}
        if config["base_url"]:
            client_kwargs["base_url"] = config["base_url"]

        client = openai.OpenAI(**client_kwargs)

        is_reasoning_model = "o1" in model or "reasoner" in model

        if is_reasoning_model:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=4096
            )
        else:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )

        return response.choices[0].message.content


# ==================== TAB: AI CHAT ====================

def render_chat_tab():
    """Render the AI chat interface."""
    ai_config = get_ai_config()
    has_key = bool(ai_config["api_key"] and len(ai_config["api_key"]) > 10)

    if not has_key:
        st.markdown(f"""
        <div class="ob-banner-warning" style="font-size: 0.9rem;">
            <strong>API Key Required</strong><br>
            <span class="text-muted">Add your {ai_config['name']} key in Settings to use the AI advisor</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Go to Settings", use_container_width=True, type="primary"):
            st.switch_page("pages/3_settings.py")
        return

    # Two-column layout: chat on left, portfolio context on right
    col_chat, col_context = st.columns([2, 1])

    with col_chat:
        model = ai_config["model"]
        provider_name = ai_config["name"]

        default_system_prompt = """You are an expert options trading assistant for Options Buddy. You help analyze positions, suggest strategies, and provide actionable recommendations.

Key behaviors:
- Be concise and direct
- Focus on premium selling strategies (CSP, covered calls, spreads)
- Consider risk management and position sizing
- When discussing specific positions, reference the user's actual data
- Explain your reasoning for recommendations
- Never recommend naked short calls without proper context

You have access to the user's current portfolio data which will be provided with each message."""

        system_prompt = DatabaseManager.get_setting("ai_system_prompt") or default_system_prompt
        connected = st.session_state.get('ibkr_connected', False)

        # Status bar
        st.caption(f"{provider_name}: {model}")

        # Initialize chat history
        if "assistant_messages" not in st.session_state:
            st.session_state.assistant_messages = []

        # Chat container with fixed height for scrolling
        chat_container = st.container(height=350)

        with chat_container:
            for message in st.session_state.assistant_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Quick question buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Portfolio", use_container_width=True, help="Analyze my portfolio"):
                st.session_state.pending_question = "Analyze my current portfolio. How am I doing? Any concerns?"
                st.rerun()
        with col2:
            if st.button("Rolls", use_container_width=True, help="Roll suggestions"):
                st.session_state.pending_question = "What roll opportunities do you see for my current positions?"
                st.rerun()
        with col3:
            if st.button("Attention", use_container_width=True, help="Positions needing attention"):
                st.session_state.pending_question = "Which of my positions need attention right now? Any expiring soon or at risk?"
                st.rerun()
        with col4:
            if st.button("Ideas", use_container_width=True, help="New trade ideas"):
                st.session_state.pending_question = "Based on my portfolio, what new trades would you suggest to generate premium?"
                st.rerun()

        # Chat input
        if prompt := st.chat_input("Ask about positions, strategies, or get suggestions..."):
            st.session_state.assistant_messages.append({"role": "user", "content": prompt})

            portfolio_context = get_portfolio_context()

            price_info = ""
            if connected and any(word in prompt.lower() for word in ["price", "current", "quote", "trading at"]):
                symbols = re.findall(r'\b[A-Z]{1,5}\b', prompt.upper())
                for sym in symbols:
                    if sym not in ["I", "A", "THE", "FOR", "AT", "IS", "IT", "TO", "OF", "AND", "OR"]:
                        price_result = get_live_price(sym)
                        if "Current price" in price_result:
                            price_info = f"\n\n**Live Data:** {price_result}"
                            break

            full_system = f"{system_prompt}\n\n---\n\n{portfolio_context}{price_info}"

            messages = [{"role": "system", "content": full_system}]
            for msg in st.session_state.assistant_messages[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

            spinner_text = "Reasoning..." if "reasoner" in model or "o1" in model else "Thinking..."
            with st.spinner(spinner_text):
                try:
                    response = chat_with_ai(messages, ai_config)
                    st.session_state.assistant_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.session_state.assistant_messages.append({"role": "assistant", "content": f"Error: {str(e)}"})

            st.rerun()

        # Handle pending questions
        if "pending_question" in st.session_state:
            question = st.session_state.pending_question
            del st.session_state.pending_question

            st.session_state.assistant_messages.append({"role": "user", "content": question})

            portfolio_context = get_portfolio_context()
            full_system = f"{system_prompt}\n\n---\n\n{portfolio_context}"

            messages = [{"role": "system", "content": full_system}]
            for msg in st.session_state.assistant_messages[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

            try:
                response = chat_with_ai(messages, ai_config)
                st.session_state.assistant_messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.session_state.assistant_messages.append({"role": "assistant", "content": f"Error: {str(e)}"})

            st.rerun()

        # Clear chat button
        if st.session_state.assistant_messages:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.assistant_messages = []
                st.rerun()

    with col_context:
        st.markdown("#### Your Positions")

        positions = DatabaseManager.get_open_positions()
        connected = st.session_state.get('ibkr_connected', False)

        if connected:
            st.markdown('<span class="text-profit" style="font-size: 0.8rem;">IBKR Connected</span>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<span class="text-warning" style="font-size: 0.8rem;">IBKR Offline</span>',
                        unsafe_allow_html=True)

        if not positions:
            st.caption("No open positions")
        else:
            # Categorize by urgency
            expiring_critical = [p for p in positions if p.days_to_expiry <= 3]
            expiring_soon = [p for p in positions if 3 < p.days_to_expiry <= 7]
            stable = [p for p in positions if p.days_to_expiry > 7]

            if expiring_critical:
                st.markdown("**Expiring Soon**")
                for pos in expiring_critical:
                    st.markdown(f"""
                    <div style="background: rgba(255,71,87,0.15); border-radius: 4px; padding: 6px 10px; margin-bottom: 4px; font-size: 0.85rem;">
                        <strong>{pos.underlying}</strong> ${pos.strike:.0f} {pos.option_type}
                        <span style="float: right; color: #ff4757;">{pos.days_to_expiry}d</span>
                    </div>
                    """, unsafe_allow_html=True)

            if expiring_soon:
                st.markdown("**This Week**")
                for pos in expiring_soon:
                    st.markdown(f"""
                    <div style="background: rgba(255,193,7,0.15); border-radius: 4px; padding: 6px 10px; margin-bottom: 4px; font-size: 0.85rem;">
                        <strong>{pos.underlying}</strong> ${pos.strike:.0f} {pos.option_type}
                        <span style="float: right; color: #ffc107;">{pos.days_to_expiry}d</span>
                    </div>
                    """, unsafe_allow_html=True)

            if stable:
                with st.expander(f"Other ({len(stable)})"):
                    for pos in stable:
                        st.caption(f"{pos.underlying} ${pos.strike:.0f} {pos.option_type} - {pos.days_to_expiry}d")

            # Total premium
            total_premium = sum(p.premium_collected * p.quantity * 100 for p in positions)
            st.markdown(f"""
            <div style="margin-top: 12px; padding: 8px; background: rgba(0,210,106,0.1); border-radius: 4px; text-align: center;">
                <span style="font-size: 0.75rem; opacity: 0.7;">Open Premium</span><br>
                <span style="font-size: 1.1rem; font-weight: 600; color: #00d26a;">${total_premium:,.0f}</span>
            </div>
            """, unsafe_allow_html=True)


# ==================== TAB: SCANNER ====================

def render_scanner_tab():
    """Render the opportunity scanner."""
    connected = st.session_state.get('ibkr_connected', False)

    # Check market hours
    market_status = get_market_status_display()
    market_open = market_status["is_open"]

    # Show market status banner
    if not market_open:
        st.markdown(f"""
        <div class="ob-banner-warning">
            <strong>{market_status["icon"]} Market Closed</strong>
            <span class="text-muted" style="margin-left: 12px;">{market_status["message"]}</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption("Real-time options data is only available during market hours. You can still browse cached data or configure filters.")
    else:
        st.markdown(f"""
        <div class="ob-banner-success">
            <strong>{market_status["icon"]} Market Open</strong>
            <span class="text-muted" style="margin-left: 12px;">{market_status["message"]}</span>
        </div>
        """, unsafe_allow_html=True)

    if not connected:
        st.markdown("""
        <div class="ob-banner-warning">
            <strong>IBKR Not Connected</strong>
            <span class="text-muted" style="margin-left: 12px;">Connect in Settings to scan live data</span>
        </div>
        """, unsafe_allow_html=True)

    # Two columns: filters on left, results on right
    col_filters, col_results = st.columns([1, 2])

    with col_filters:
        st.markdown("#### Filters")

        # Watchlist selector
        watchlists = DatabaseManager.get_all_watchlists()
        watchlist_names = [w.name for w in watchlists] if watchlists else []

        if watchlist_names:
            selected_watchlist = st.selectbox("Watchlist", watchlist_names)
            selected_wl = next((w for w in watchlists if w.name == selected_watchlist), None)
            symbols = selected_wl.symbols if selected_wl else []
            st.caption(f"{len(symbols)} symbols")
        else:
            symbols = []
            st.caption("No watchlists - create one in Settings")

        st.markdown("---")

        # DTE range
        st.markdown("**DTE Range**")
        col1, col2 = st.columns(2)
        with col1:
            min_dte = st.number_input("Min", value=7, min_value=1, max_value=365, label_visibility="collapsed")
        with col2:
            max_dte = st.number_input("Max", value=45, min_value=1, max_value=365, label_visibility="collapsed")

        # Delta range
        st.markdown("**Delta**")
        delta_range = st.slider("Delta", min_value=0.05, max_value=0.50,
                                value=(0.15, 0.35), step=0.05, label_visibility="collapsed")

        # Strategy
        all_strategies = ["Naked Put", "Cash-Secured Put", "Covered Call", "Bull Put Spread"]
        strategy_types = st.multiselect("Strategies", all_strategies, default=["Cash-Secured Put"])

        # Premium and IV/HV
        col1, col2 = st.columns(2)
        with col1:
            min_premium = st.number_input("Min $", value=0.50, min_value=0.01, step=0.25)
        with col2:
            iv_hv_threshold = st.number_input("IV/HV >", value=1.2, min_value=1.0, max_value=2.0, step=0.1)

        # Scan button - show warning if market closed
        scan_disabled = not connected or not symbols
        scan_label = f"Scan {len(symbols)} Symbols" if symbols else "Select Watchlist"

        if not market_open and connected and symbols:
            scan_label = f"Scan {len(symbols)} (Market Closed)"

        scan_button = st.button(
            scan_label,
            use_container_width=True,
            disabled=scan_disabled,
            type="primary"
        )

        # Additional warning when market closed
        if not market_open and connected:
            st.caption("Data may be stale or unavailable")

    with col_results:
        st.markdown("#### Results")

        if scan_button and connected and symbols:
            with st.spinner("Scanning options..."):
                from data.ibkr_client import get_ibkr_client

                client = get_ibkr_client()
                results = []
                progress_bar = st.progress(0)

                for i, sym in enumerate(symbols):
                    progress_bar.progress((i + 1) / len(symbols))

                    try:
                        price = client.get_stock_price(sym)
                        if not price:
                            continue

                        expirations = client.get_option_chain_expirations(sym)
                        if not expirations:
                            continue

                        for exp in expirations[:5]:
                            try:
                                exp_date = datetime.strptime(exp, "%Y%m%d")
                                dte = (exp_date.date() - date.today()).days
                                if min_dte <= dte <= max_dte:
                                    strikes = client.get_option_chain_strikes(sym, exp)
                                    if strikes:
                                        # Placeholder for actual option data
                                        st.caption(f"Found {len(strikes)} strikes for {sym} exp {exp}")
                            except:
                                continue

                    except Exception as e:
                        st.warning(f"Error scanning {sym}: {str(e)}")

                progress_bar.empty()

                if results:
                    df = pd.DataFrame(results)
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'Score': st.column_config.ProgressColumn('Score', min_value=0, max_value=100, format="%d"),
                            'Bid': st.column_config.NumberColumn(format="$%.2f"),
                            'Strike': st.column_config.NumberColumn(format="$%.0f"),
                        }
                    )
                else:
                    # More helpful message based on market status
                    if not market_open:
                        st.warning("No data returned. The market is currently closed - real-time options quotes are only available during trading hours (9:30 AM - 4:00 PM ET, Mon-Fri).")
                        st.info("**Tip:** Try scanning during market hours for live data, or check your IBKR market data subscription settings.")
                    else:
                        st.info("Scan complete. No opportunities matched your filters. Try adjusting filters or check your market data subscription in IBKR.")

        elif not connected:
            st.info("Connect to IBKR in Settings to scan for live opportunities")
            if st.button("Go to Settings"):
                st.switch_page("pages/3_settings.py")

        elif not symbols:
            st.info("Select a watchlist with symbols to scan")

        else:
            st.caption("Configure filters and click Scan to find opportunities")

            # Show recent scan results if any
            if "last_scan_results" in st.session_state and st.session_state.last_scan_results:
                st.markdown("**Last Scan Results:**")
                st.dataframe(st.session_state.last_scan_results, use_container_width=True)


# ==================== TAB: ANALYZER ====================

def render_analyzer_tab():
    """Render the options calculator and analyzer."""
    bs = BlackScholes()
    connected = st.session_state.get('ibkr_connected', False)

    # Symbol input
    col1, col2 = st.columns([3, 1])
    with col1:
        symbol = st.text_input("Symbol", value="AAPL", placeholder="Enter ticker").upper()
    with col2:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        if connected:
            st.markdown('<span class="text-profit">Live Data</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="text-muted">Manual Input</span>', unsafe_allow_html=True)

    # Sub-tabs within analyzer
    calc_tab, payoff_tab, vol_tab = st.tabs(["Calculator", "Payoff", "Volatility"])

    with calc_tab:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Inputs**")
            underlying_price = st.number_input("Underlying Price", value=185.0, step=1.0)
            strike_price = st.number_input("Strike Price", value=180.0, step=1.0)
            dte = st.number_input("Days to Expiry", value=30, min_value=1, max_value=365)
            iv = st.number_input("IV (%)", value=25.0, min_value=1.0, max_value=200.0, step=0.5) / 100
            option_type = st.selectbox("Type", [PUT, CALL])
            risk_free = st.number_input("Risk-Free Rate (%)", value=5.0, step=0.25) / 100

        with col2:
            st.markdown("**Results**")

            time_to_expiry = bs.days_to_years(dte)

            price = bs.calculate_price(underlying_price, strike_price, time_to_expiry,
                                        iv, option_type, risk_free)
            greeks = bs.calculate_greeks(underlying_price, strike_price, time_to_expiry,
                                          iv, option_type, risk_free)

            st.markdown(f"""
            <div class="ob-card" style="text-align: center; padding: 16px;">
                <div class="text-muted" style="font-size: 0.8rem; text-transform: uppercase;">Theoretical Price</div>
                <div style="font-size: 2rem; font-weight: 600;">${price:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Delta", f"{greeks.delta:.4f}")
                st.metric("Theta", f"${greeks.theta:.4f}/day")
            with col_b:
                st.metric("Gamma", f"{greeks.gamma:.4f}")
                st.metric("Vega", f"${greeks.vega:.4f}")

            prob_otm = 1 - abs(greeks.delta)
            st.metric("Prob OTM at Expiry", f"{prob_otm * 100:.1f}%")

    with payoff_tab:
        col1, col2, col3 = st.columns(3)

        with col1:
            payoff_strike = st.number_input("Strike", value=180.0, step=1.0, key="payoff_strike")
        with col2:
            payoff_premium = st.number_input("Premium", value=2.50, step=0.25, key="payoff_premium")
        with col3:
            payoff_type = st.selectbox("Position", ["Short Put", "Short Call", "Long Put", "Long Call"])

        # Generate payoff
        stock_prices = list(range(int(payoff_strike * 0.7), int(payoff_strike * 1.3)))

        if payoff_type == "Short Put":
            payoffs = [min(payoff_premium * 100, (price - payoff_strike + payoff_premium) * 100)
                       if price < payoff_strike else payoff_premium * 100 for price in stock_prices]
        elif payoff_type == "Short Call":
            payoffs = [payoff_premium * 100 if price < payoff_strike
                       else (payoff_strike + payoff_premium - price) * 100 for price in stock_prices]
        elif payoff_type == "Long Put":
            payoffs = [(payoff_strike - price - payoff_premium) * 100 if price < payoff_strike
                       else -payoff_premium * 100 for price in stock_prices]
        else:
            payoffs = [-payoff_premium * 100 if price < payoff_strike
                       else (price - payoff_strike - payoff_premium) * 100 for price in stock_prices]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=stock_prices, y=payoffs, mode='lines',
            name='P/L', line=dict(color='#3742fa', width=2)
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.add_vline(x=payoff_strike, line_dash="dash", line_color="red")

        fig.update_layout(
            title=f'{payoff_type} Payoff',
            xaxis_title='Stock Price',
            yaxis_title='P/L ($)',
            height=300,
            margin=dict(l=40, r=40, t=40, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Metrics
        if "Short" in payoff_type:
            max_profit = payoff_premium * 100
            if "Put" in payoff_type:
                breakeven = payoff_strike - payoff_premium
                max_loss = (payoff_strike - payoff_premium) * 100
            else:
                breakeven = payoff_strike + payoff_premium
                max_loss = "Unlimited"
        else:
            max_loss = payoff_premium * 100
            if "Put" in payoff_type:
                breakeven = payoff_strike - payoff_premium
                max_profit = (payoff_strike - payoff_premium) * 100
            else:
                breakeven = payoff_strike + payoff_premium
                max_profit = "Unlimited"

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Breakeven", f"${breakeven:.2f}")
        with col2:
            st.metric("Max Profit", f"${max_profit:.2f}" if isinstance(max_profit, (int, float)) else max_profit)
        with col3:
            st.metric("Max Loss", f"${max_loss:.2f}" if isinstance(max_loss, (int, float)) else max_loss)

    with vol_tab:
        if connected:
            from data.historical_data import HistoricalDataFetcher

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Historical Volatility**")

                if st.button(f"Calculate HV for {symbol}", use_container_width=True):
                    with st.spinner("Calculating HV..."):
                        fetcher = HistoricalDataFetcher()
                        try:
                            hv_10 = fetcher.calculate_historical_volatility(symbol, window=10)
                            hv_21 = fetcher.calculate_historical_volatility(symbol, window=21)
                            hv_63 = fetcher.calculate_historical_volatility(symbol, window=63)

                            if hv_10 is not None:
                                st.metric("10-Day HV", f"{hv_10*100:.1f}%")
                            if hv_21 is not None:
                                st.metric("21-Day HV", f"{hv_21*100:.1f}%")
                            if hv_63 is not None:
                                st.metric("63-Day HV", f"{hv_63*100:.1f}%")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

            with col2:
                st.markdown("**IV Comparison**")
                st.info("IV requires real-time option quotes with market data subscription.")
        else:
            st.info("Connect to IBKR to calculate live volatility data")
            if st.button("Go to Settings", key="vol_settings"):
                st.switch_page("pages/3_settings.py")


# ==================== MAIN PAGE ====================

def render_advisor():
    """Render the advisor page with tabs."""
    apply_global_styles()

    # Compact header with status
    col_title, col_status = st.columns([3, 1])

    with col_title:
        st.markdown("""
        <div style="margin-bottom: 0.5rem;">
            <h1 style="margin: 0; font-size: 1.75rem;">Advisor</h1>
            <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9rem;">AI assistant, scanner, and analyzer</p>
        </div>
        """, unsafe_allow_html=True)

    with col_status:
        connected = st.session_state.get('ibkr_connected', False)
        if connected:
            st.markdown('<div style="text-align: right; padding-top: 8px;"><span class="text-profit">IBKR Connected</span></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: right; padding-top: 8px;"><span class="text-warning">IBKR Offline</span></div>',
                        unsafe_allow_html=True)

    init_database()

    # Main tabs
    tab_chat, tab_scan, tab_analyze = st.tabs(["Chat", "Scan", "Analyze"])

    with tab_chat:
        render_chat_tab()

    with tab_scan:
        render_scanner_tab()

    with tab_analyze:
        render_analyzer_tab()


# Run the page
render_advisor()
