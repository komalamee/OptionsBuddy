"""
Analyzer Page - Deep-dive option analysis for a specific symbol.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime

from database import init_database
from core.black_scholes import BlackScholes
from config.constants import CALL, PUT
from components.styles import apply_global_styles, COLORS


def render_analyzer():
    """Render the analyzer page."""
    # Apply global styles
    apply_global_styles()

    # Compact header
    st.markdown("""
    <div style="margin-bottom: 0.75rem;">
        <h1 style="margin: 0; font-size: 1.75rem;">Option Analyzer</h1>
        <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9rem;">Deep-dive analysis for individual symbols</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize
    init_database()
    bs = BlackScholes()

    # Check connection
    connected = st.session_state.get('ibkr_connected', False)

    # Symbol input row - compact
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        symbol = st.text_input("Symbol", value="AAPL", placeholder="Enter ticker",
                                label_visibility="collapsed").upper()

    with col2:
        if connected:
            st.markdown('<span style="color: #2ed573; font-size: 0.85rem;">Connected</span>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<span style="color: #ffa502; font-size: 0.85rem;">Offline</span>',
                        unsafe_allow_html=True)

    with col3:
        analyze_btn = st.button("Analyze", use_container_width=True, type="primary")

    if symbol:
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Option Chain", "Volatility", "Calculator", "Payoff"])

        with tab1:
            st.markdown(f"#### Option Chain: {symbol}")

            if connected:
                from data.ibkr_client import get_ibkr_client
                client = get_ibkr_client()

                with st.spinner(f"Fetching options for {symbol}..."):
                    expirations = client.get_option_chain_expirations(symbol)

                if expirations:
                    selected_expiry = st.selectbox(
                        "Expiration",
                        expirations,
                        format_func=lambda x: f"{x[:4]}-{x[4:6]}-{x[6:]}" if len(x) == 8 else x
                    )

                    if selected_expiry:
                        strikes = client.get_option_chain_strikes(symbol, selected_expiry)
                        if strikes:
                            st.info(f"Found {len(strikes)} strikes. Full chain data requires market data subscription.")
                            st.caption(f"Strikes: {strikes[:10]}..." if len(strikes) > 10 else f"Strikes: {strikes}")
                        else:
                            st.warning("No strikes found.")
                else:
                    st.warning(f"No options found for {symbol}.")
            else:
                _show_connect_prompt("option chain")

        with tab2:
            st.markdown(f"#### Volatility: {symbol}")

            if connected:
                from data.historical_data import HistoricalDataFetcher

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Historical Volatility**")

                    with st.spinner("Calculating HV..."):
                        fetcher = HistoricalDataFetcher()
                        try:
                            hv_10 = fetcher.calculate_historical_volatility(symbol, window=10)
                            hv_21 = fetcher.calculate_historical_volatility(symbol, window=21)
                            hv_63 = fetcher.calculate_historical_volatility(symbol, window=63)

                            metrics = []
                            if hv_10 is not None:
                                metrics.append(("10-Day", f"{hv_10*100:.1f}%"))
                            if hv_21 is not None:
                                metrics.append(("21-Day", f"{hv_21*100:.1f}%"))
                            if hv_63 is not None:
                                metrics.append(("63-Day", f"{hv_63*100:.1f}%"))

                            if metrics:
                                for label, value in metrics:
                                    st.metric(label, value)
                            else:
                                st.warning("Insufficient data for HV calculation.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

                with col2:
                    st.markdown("**IV Comparison**")
                    st.info("IV requires real-time option quotes.")

                st.markdown("**Volatility Chart**")
                st.info("Chart displays with sufficient price history.")

            else:
                _show_connect_prompt("volatility analysis")

        with tab3:
            st.markdown("#### Options Calculator")

            col1, col2 = st.columns(2)

            with col1:
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

                # Display in compact grid
                st.markdown(f"""
                <div style="
                    background: rgba(55, 66, 250, 0.1);
                    border-radius: 8px;
                    padding: 16px;
                    margin-bottom: 12px;
                ">
                    <div style="font-size: 0.8rem; opacity: 0.7; text-transform: uppercase;">Theoretical Price</div>
                    <div style="font-size: 1.5rem; font-weight: 600;">${price:.2f}</div>
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

        with tab4:
            st.markdown("#### Payoff Diagram")

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

            # Chart
            fig = go.Figure()

            # Color based on profit/loss
            colors = ['#00d26a' if p > 0 else '#ff4757' for p in payoffs]

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
                height=350,
                margin=dict(l=40, r=40, t=40, b=40),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Metrics row
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


def _show_connect_prompt(feature: str):
    """Show compact connect to IBKR prompt."""
    st.markdown(f"""
    <div style="
        background: rgba(128, 128, 128, 0.1);
        border: 1px dashed rgba(128, 128, 128, 0.3);
        border-radius: 8px;
        padding: 30px;
        text-align: center;
    ">
        <p style="opacity: 0.7; margin: 0;">Connect to IBKR to view {feature}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("Go to Settings", key=f"goto_settings_{feature.replace(' ', '_')}"):
            st.switch_page("pages/6_settings.py")


# Run the page
render_analyzer()
