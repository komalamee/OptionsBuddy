"""
Dashboard - Main hub with portfolio overview and AI assistant.
Professional trading UI with dark/light mode support.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import DatabaseManager, init_database
from components.theme import apply_theme, metric_card, page_header, status_badge, ai_message


def render_connection_status():
    """Render the IBKR connection status indicator."""
    connected = st.session_state.get('ibkr_connected', False)

    if connected:
        st.markdown('''
        <div class="ob-status-indicator ob-status-connected">
            <span style="width: 8px; height: 8px; background: var(--profit); border-radius: 50%;"></span>
            Connected
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div class="ob-status-indicator ob-status-disconnected">
            <span style="width: 8px; height: 8px; background: var(--loss); border-radius: 50%;"></span>
            Disconnected
        </div>
        ''', unsafe_allow_html=True)


def render_portfolio_metrics():
    """Render the top portfolio metrics row."""
    # Get data
    open_positions = DatabaseManager.get_open_positions()
    realized_pnl = DatabaseManager.calculate_realized_pnl()
    open_premium = DatabaseManager.calculate_open_premium()
    stats = DatabaseManager.get_position_stats()
    portfolio_summary = DatabaseManager.get_portfolio_summary()

    pnl_value = realized_pnl['total_pnl']
    win_rate = stats.get('win_rate', 0)
    total_trades = realized_pnl.get('closed_count', 0)

    # Calculate total portfolio value (stocks + open premium)
    stock_value = portfolio_summary.get('total_stock_value', 0) or 0
    total_value = stock_value + open_premium

    # Hero metric - Total Portfolio Value
    col_hero, col_metrics = st.columns([1, 2])

    with col_hero:
        pnl_class = "profit" if pnl_value >= 0 else "loss"
        pnl_sign = "+" if pnl_value >= 0 else ""
        st.markdown(f'''
        <div class="ob-metric-hero">
            <div class="ob-metric-label">Portfolio Value</div>
            <div class="ob-metric-value">${total_value:,.2f}</div>
            <div class="ob-metric-delta {'positive' if pnl_value >= 0 else 'negative'}">
                {pnl_sign}${pnl_value:,.2f} realized P&L
            </div>
        </div>
        ''', unsafe_allow_html=True)

    with col_metrics:
        # Grid of smaller metrics
        st.markdown(f'''
        <div class="ob-metrics-row">
            <div class="ob-metric">
                <div class="ob-metric-label">Open Positions</div>
                <div class="ob-metric-value">{len(open_positions)}</div>
            </div>
            <div class="ob-metric">
                <div class="ob-metric-label">Open Premium</div>
                <div class="ob-metric-value">${open_premium:,.0f}</div>
            </div>
            <div class="ob-metric">
                <div class="ob-metric-label">Win Rate</div>
                <div class="ob-metric-value">{win_rate:.0f}%</div>
            </div>
            <div class="ob-metric">
                <div class="ob-metric-label">Total Trades</div>
                <div class="ob-metric-value">{total_trades}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)


def get_ai_context():
    """Build context for AI assistant about user's portfolio."""
    positions = DatabaseManager.get_open_positions()
    stats = DatabaseManager.get_position_stats()
    holdings = DatabaseManager.get_all_stock_holdings()

    context_parts = []

    if positions:
        expiring_soon = [p for p in positions if p.days_to_expiry <= 7]
        context_parts.append(f"User has {len(positions)} open positions")
        if expiring_soon:
            context_parts.append(f"{len(expiring_soon)} expiring within 7 days")

    if holdings:
        context_parts.append(f"{len(holdings)} stock holdings")

    return ". ".join(context_parts) if context_parts else "No positions yet"


def render_ai_assistant():
    """Render the AI assistant panel - central feature of the dashboard."""
    # Initialize chat history
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

    st.markdown('''
    <div class="ob-ai-panel">
        <div class="ob-ai-header">
            <div class="ob-ai-icon">🤖</div>
            <div>
                <h3 class="ob-ai-title">AI Market Advisor</h3>
                <p class="ob-ai-subtitle">Your intelligent options trading assistant</p>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Chat area
    chat_container = st.container()

    with chat_container:
        # Display chat messages
        if st.session_state.chat_messages:
            for msg in st.session_state.chat_messages[-10:]:  # Last 10 messages
                if msg['role'] == 'user':
                    st.markdown(f'''
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                        <div style="background: var(--primary, #3B82F6); color: white; padding: 12px 16px; border-radius: 12px 12px 4px 12px; max-width: 80%;">
                            {msg['content']}
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
                        <div style="background: var(--card, #334155); padding: 12px 16px; border-radius: 12px 12px 12px 4px; max-width: 80%;">
                            {msg['content']}
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
        else:
            # Welcome message
            portfolio_context = get_ai_context()
            st.markdown(f'''
            <div style="background: rgba(59, 130, 246, 0.1); border-radius: 12px; padding: 20px; margin-bottom: 16px;">
                <p style="margin: 0 0 8px 0; font-weight: 600;">Welcome! I'm your AI options advisor.</p>
                <p style="margin: 0; color: var(--text-muted, #94A3B8); font-size: 0.9rem;">
                    {portfolio_context}. Ask me about trade ideas, position management, or market analysis.
                </p>
            </div>
            ''', unsafe_allow_html=True)

    # Input area
    col_input, col_btn = st.columns([5, 1])

    with col_input:
        user_input = st.text_input(
            "Ask the AI",
            placeholder="Ask about trade ideas, position management, or market analysis...",
            label_visibility="collapsed",
            key="ai_input"
        )

    with col_btn:
        send_clicked = st.button("Send", type="primary", use_container_width=True)

    # Quick suggestion chips
    st.markdown('''
    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px;">
    ''', unsafe_allow_html=True)

    suggestions = [
        "What positions need attention?",
        "Find covered call opportunities",
        "Analyze my portfolio risk",
        "Best trades for this week"
    ]

    cols = st.columns(len(suggestions))
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                user_input = suggestion

    st.markdown('</div>', unsafe_allow_html=True)

    # Handle send
    if (send_clicked or user_input) and user_input:
        # Add user message
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': user_input
        })

        # Generate AI response (placeholder - integrate with actual AI)
        response = generate_ai_response(user_input)
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': response
        })

        st.rerun()


def generate_ai_response(query: str) -> str:
    """Generate AI response based on query and portfolio context."""
    query_lower = query.lower()

    positions = DatabaseManager.get_open_positions()
    holdings = DatabaseManager.get_all_stock_holdings()

    # Position attention queries
    if "attention" in query_lower or "expiring" in query_lower:
        expiring = [p for p in positions if p.days_to_expiry <= 7]
        if expiring:
            response = f"**{len(expiring)} position(s) need attention:**\n\n"
            for p in expiring[:5]:
                response += f"- **{p.underlying}** ${p.strike} {p.option_type} - {p.days_to_expiry} days left\n"
            return response
        return "All your positions look good! No urgent attention needed."

    # Covered call opportunities
    if "covered call" in query_lower:
        cc_eligible = DatabaseManager.get_covered_call_eligible()
        if cc_eligible:
            response = "**Covered call opportunities:**\n\n"
            for stock in cc_eligible[:5]:
                response += f"- **{stock['symbol']}** - {stock['cc_lots']} lot(s) available ({stock['quantity']} shares)\n"
            return response
        return "No stocks with 100+ shares for covered calls. Consider building positions first."

    # Portfolio risk
    if "risk" in query_lower or "portfolio" in query_lower:
        if positions:
            by_underlying = {}
            for p in positions:
                by_underlying[p.underlying] = by_underlying.get(p.underlying, 0) + 1

            response = "**Portfolio Analysis:**\n\n"
            response += f"- {len(positions)} open positions across {len(by_underlying)} underlyings\n"

            max_concentration = max(by_underlying.values()) if by_underlying else 0
            if max_concentration > 3:
                response += f"- **Warning:** High concentration detected\n"
            else:
                response += f"- Diversification looks reasonable\n"

            return response
        return "No open positions to analyze. Start with the Scanner to find opportunities!"

    # Best trades
    if "best" in query_lower or "trade" in query_lower or "ideas" in query_lower:
        return """**Trade Ideas for This Week:**

Based on current market conditions, consider:

1. **High IV Plays** - Look for elevated IV rank (>50%) for premium selling
2. **Wheel Strategy** - CSPs on quality stocks you'd own
3. **Covered Calls** - Generate income on existing holdings

Use the **Scanner** tab to find specific opportunities matching your criteria."""

    # Default response
    return """I can help you with:

- **Position Management** - "What positions need attention?"
- **Trade Ideas** - "Find covered call opportunities"
- **Risk Analysis** - "Analyze my portfolio risk"
- **Market Insights** - "Best trades for this week"

What would you like to explore?"""


def render_positions_summary():
    """Render a compact positions summary."""
    positions = DatabaseManager.get_open_positions()

    st.markdown('''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">Open Positions</h3>
            <span class="ob-card-action">View All →</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if positions:
        # Show top 5 positions
        for pos in positions[:5]:
            dte = pos.days_to_expiry
            dte_color = "text-loss" if dte <= 3 else "text-warning" if dte <= 7 else "text-muted"
            badge_class = "ob-badge-loss" if dte <= 3 else "ob-badge-warning" if dte <= 7 else "ob-badge-info"

            st.markdown(f'''
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: var(--card, #334155); border-radius: 8px; margin-bottom: 8px;">
                <div>
                    <span style="font-weight: 600; font-size: 1rem;">{pos.underlying}</span>
                    <span style="color: var(--text-muted); margin-left: 8px;">${pos.strike:.0f} {pos.option_type}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span class="{dte_color}" style="font-weight: 500;">{dte}d</span>
                    <span style="color: var(--text-muted);">${pos.premium_collected:.2f}</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        if len(positions) > 5:
            st.caption(f"+ {len(positions) - 5} more positions")

        # Quick action
        if st.button("View All Positions", use_container_width=True):
            st.switch_page("pages/2_positions.py")
    else:
        st.markdown('''
        <div style="text-align: center; padding: 40px; color: var(--text-muted);">
            <p style="font-size: 2rem; margin-bottom: 8px;">📊</p>
            <p>No open positions yet</p>
        </div>
        ''', unsafe_allow_html=True)

        if st.button("Find Opportunities", type="primary", use_container_width=True):
            st.switch_page("pages/2_advisor.py")


def render_stock_holdings_summary():
    """Render a compact stock holdings summary."""
    holdings = DatabaseManager.get_all_stock_holdings()
    portfolio_summary = DatabaseManager.get_portfolio_summary()

    if not holdings:
        return

    st.markdown('''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">Stock Holdings</h3>
            <span class="ob-card-action">Manage →</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Summary stats
    total_value = portfolio_summary.get('total_stock_value', 0) or 0
    cc_lots = portfolio_summary.get('cc_lots_available', 0)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'''
        <div style="text-align: center; padding: 12px; background: var(--card); border-radius: 8px;">
            <div style="font-size: 1.25rem; font-weight: 700;">${total_value:,.0f}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">MARKET VALUE</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
        <div style="text-align: center; padding: 12px; background: var(--card); border-radius: 8px;">
            <div style="font-size: 1.25rem; font-weight: 700;">{int(cc_lots)}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">CC LOTS READY</div>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # Top holdings
    for h in holdings[:4]:
        lots = h.quantity // 100
        st.markdown(f'''
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: var(--card, #334155); border-radius: 8px; margin-bottom: 6px;">
            <div>
                <span style="font-weight: 600;">{h.symbol}</span>
                <span style="color: var(--text-muted); margin-left: 8px; font-size: 0.85rem;">{h.quantity} shares</span>
            </div>
            <div>
                {f'<span class="ob-badge ob-badge-profit">{lots} lots</span>' if lots > 0 else ''}
            </div>
        </div>
        ''', unsafe_allow_html=True)


def render_alerts_panel():
    """Render alerts and notifications panel."""
    positions = DatabaseManager.get_open_positions()
    critical = [p for p in positions if p.days_to_expiry <= 3]
    warning = [p for p in positions if 3 < p.days_to_expiry <= 7]

    st.markdown('''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">Alerts</h3>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if critical:
        for p in critical:
            st.markdown(f'''
            <div style="background: var(--loss-bg); border-left: 3px solid var(--loss); border-radius: 0 8px 8px 0; padding: 12px 16px; margin-bottom: 8px;">
                <div style="font-weight: 600; color: var(--loss);">🚨 EXPIRING</div>
                <div style="font-size: 0.9rem; margin-top: 4px;">
                    <strong>{p.underlying}</strong> ${p.strike:.0f} {p.option_type} - {p.days_to_expiry}d left
                </div>
            </div>
            ''', unsafe_allow_html=True)

    if warning:
        for p in warning[:3]:  # Max 3 warnings
            st.markdown(f'''
            <div style="background: var(--warning-bg); border-left: 3px solid var(--warning); border-radius: 0 8px 8px 0; padding: 12px 16px; margin-bottom: 8px;">
                <div style="font-weight: 600; color: var(--warning);">⚠️ WATCH</div>
                <div style="font-size: 0.9rem; margin-top: 4px;">
                    <strong>{p.underlying}</strong> ${p.strike:.0f} {p.option_type} - {p.days_to_expiry}d left
                </div>
            </div>
            ''', unsafe_allow_html=True)

    if not critical and not warning:
        st.markdown('''
        <div style="text-align: center; padding: 24px; color: var(--profit);">
            <p style="font-size: 1.5rem; margin-bottom: 4px;">✓</p>
            <p style="margin: 0;">All clear!</p>
        </div>
        ''', unsafe_allow_html=True)


def render_quick_actions():
    """Render quick action buttons."""
    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔍 Scanner", use_container_width=True):
            st.switch_page("pages/2_advisor.py")

    with col2:
        if st.button("📊 Positions", use_container_width=True):
            st.switch_page("pages/2_positions.py")

    with col3:
        if st.button("💡 Trade Ideas", use_container_width=True):
            st.switch_page("pages/3_ideas.py")

    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.switch_page("pages/5_settings.py")


def render_dashboard():
    """Render the main dashboard."""
    # Apply theme
    apply_theme()

    # Initialize database
    init_database()

    # Page header with connection status
    col_title, col_status = st.columns([4, 1])

    with col_title:
        st.markdown(page_header("Dashboard", "Portfolio overview and AI-powered insights"), unsafe_allow_html=True)

    with col_status:
        render_connection_status()

    # Portfolio metrics row
    render_portfolio_metrics()

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    # Main content: AI Assistant (left) + Sidebar panels (right)
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # AI Assistant - central feature
        render_ai_assistant()

    with col_side:
        # Alerts panel
        render_alerts_panel()

        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

        # Positions summary
        render_positions_summary()

        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

        # Stock holdings (if any)
        render_stock_holdings_summary()

    # Quick actions at bottom
    render_quick_actions()


# Run the page
render_dashboard()
