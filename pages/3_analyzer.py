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


def render_analyzer():
    """Render the analyzer page."""
    st.title("📊 Option Analyzer")
    st.markdown("Deep-dive analysis for individual symbols")

    # Initialize
    init_database()
    bs = BlackScholes()

    # Check connection
    connected = st.session_state.get('ibkr_connected', False)

    # Symbol input
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        symbol = st.text_input(
            "Symbol",
            value="AAPL",
            placeholder="Enter ticker symbol"
        ).upper()

    with col2:
        if connected:
            st.success("🟢 Connected")
        else:
            st.warning("🔴 Offline")

    with col3:
        analyze_btn = st.button("🔍 Analyze", use_container_width=True)

    st.markdown("---")

    if symbol:
        # Tabs for different analyses
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Option Chain",
            "📊 Volatility",
            "🧮 Calculator",
            "💰 Payoff Diagram"
        ])

        with tab1:
            st.subheader(f"Option Chain: {symbol}")

            if connected:
                st.info("Option chain data will load from IBKR when connected.")
            else:
                st.warning("Connect to IBKR to view live option chains.")

                # Show example chain
                with st.expander("Example Option Chain (Demo Data)"):
                    example_chain = pd.DataFrame({
                        'Strike': [170, 175, 180, 185, 190],
                        'Call Bid': [15.20, 11.50, 8.30, 5.60, 3.40],
                        'Call Ask': [15.40, 11.70, 8.50, 5.80, 3.60],
                        'Put Bid': [0.85, 1.45, 2.40, 3.80, 5.70],
                        'Put Ask': [0.90, 1.50, 2.50, 3.95, 5.85],
                        'Call Delta': [0.82, 0.72, 0.58, 0.42, 0.28],
                        'Put Delta': [-0.18, -0.28, -0.42, -0.58, -0.72]
                    })
                    st.dataframe(example_chain, use_container_width=True, hide_index=True)

        with tab2:
            st.subheader(f"Volatility Analysis: {symbol}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Historical Volatility")

                if connected:
                    st.info("HV calculations will load from IBKR data.")
                else:
                    # Placeholder volatility data
                    vol_data = {
                        '10-Day HV': '24.5%',
                        '21-Day HV': '26.2%',
                        '63-Day HV': '28.1%',
                        '252-Day HV': '31.4%'
                    }
                    for period, value in vol_data.items():
                        st.metric(period, value)

            with col2:
                st.markdown("### Volatility Comparison")

                # Placeholder comparison
                st.metric("Current IV (ATM)", "28.5%")
                st.metric("21-Day HV", "26.2%")
                st.metric("IV/HV Ratio", "1.09", delta="9% premium")

            # Volatility chart placeholder
            st.markdown("### IV vs HV Over Time")

            if connected:
                st.info("Chart will display when connected to IBKR.")
            else:
                # Create placeholder chart
                dates = pd.date_range(end=date.today(), periods=60)
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=dates,
                    y=[25 + i * 0.1 + (i % 5) for i in range(60)],
                    name='IV',
                    line=dict(color='blue')
                ))

                fig.add_trace(go.Scatter(
                    x=dates,
                    y=[24 + i * 0.08 + (i % 7) * 0.5 for i in range(60)],
                    name='HV (21-day)',
                    line=dict(color='orange')
                ))

                fig.update_layout(
                    title='IV vs HV (Demo)',
                    xaxis_title='Date',
                    yaxis_title='Volatility (%)',
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.subheader("Options Calculator")

            st.markdown("Calculate theoretical prices and Greeks")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Inputs")

                underlying_price = st.number_input(
                    "Underlying Price",
                    value=185.0,
                    step=1.0
                )

                strike_price = st.number_input(
                    "Strike Price",
                    value=180.0,
                    step=1.0
                )

                dte = st.number_input(
                    "Days to Expiry",
                    value=30,
                    min_value=1,
                    max_value=365
                )

                iv = st.number_input(
                    "Implied Volatility (%)",
                    value=25.0,
                    min_value=1.0,
                    max_value=200.0,
                    step=0.5
                ) / 100

                option_type = st.selectbox(
                    "Option Type",
                    [PUT, CALL]
                )

                risk_free = st.number_input(
                    "Risk-Free Rate (%)",
                    value=5.0,
                    step=0.25
                ) / 100

            with col2:
                st.markdown("### Results")

                # Calculate using Black-Scholes
                time_to_expiry = bs.days_to_years(dte)

                price = bs.calculate_price(
                    underlying_price,
                    strike_price,
                    time_to_expiry,
                    iv,
                    option_type,
                    risk_free
                )

                greeks = bs.calculate_greeks(
                    underlying_price,
                    strike_price,
                    time_to_expiry,
                    iv,
                    option_type,
                    risk_free
                )

                st.metric("Theoretical Price", f"${price:.2f}")
                st.metric("Delta", f"{greeks.delta:.4f}")
                st.metric("Gamma", f"{greeks.gamma:.4f}")
                st.metric("Theta", f"${greeks.theta:.4f}/day")
                st.metric("Vega", f"${greeks.vega:.4f}")

                # Probability calculations
                prob_otm = 1 - abs(greeks.delta)
                st.metric("Prob. OTM at Expiry", f"{prob_otm * 100:.1f}%")

        with tab4:
            st.subheader("Payoff Diagram")

            st.markdown("Visualize profit/loss at expiration")

            col1, col2 = st.columns(2)

            with col1:
                payoff_strike = st.number_input(
                    "Strike",
                    value=180.0,
                    step=1.0,
                    key="payoff_strike"
                )

            with col2:
                payoff_premium = st.number_input(
                    "Premium Collected",
                    value=2.50,
                    step=0.25,
                    key="payoff_premium"
                )

            payoff_type = st.selectbox(
                "Position Type",
                ["Short Put", "Short Call", "Long Put", "Long Call"]
            )

            # Generate payoff diagram
            stock_prices = list(range(int(payoff_strike * 0.7), int(payoff_strike * 1.3)))

            if payoff_type == "Short Put":
                payoffs = [
                    min(payoff_premium * 100, (price - payoff_strike + payoff_premium) * 100)
                    if price < payoff_strike
                    else payoff_premium * 100
                    for price in stock_prices
                ]
            elif payoff_type == "Short Call":
                payoffs = [
                    payoff_premium * 100
                    if price < payoff_strike
                    else (payoff_strike + payoff_premium - price) * 100
                    for price in stock_prices
                ]
            elif payoff_type == "Long Put":
                payoffs = [
                    (payoff_strike - price - payoff_premium) * 100
                    if price < payoff_strike
                    else -payoff_premium * 100
                    for price in stock_prices
                ]
            else:  # Long Call
                payoffs = [
                    -payoff_premium * 100
                    if price < payoff_strike
                    else (price - payoff_strike - payoff_premium) * 100
                    for price in stock_prices
                ]

            # Create chart
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=stock_prices,
                y=payoffs,
                mode='lines',
                name='P/L',
                line=dict(color='blue', width=2)
            ))

            # Add break-even line
            fig.add_hline(y=0, line_dash="dash", line_color="gray")

            # Add strike line
            fig.add_vline(x=payoff_strike, line_dash="dash", line_color="red")

            fig.update_layout(
                title=f'{payoff_type} Payoff at Expiration',
                xaxis_title='Stock Price at Expiration',
                yaxis_title='Profit/Loss ($)',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # Breakeven and max profit/loss
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


# Run the page
render_analyzer()
