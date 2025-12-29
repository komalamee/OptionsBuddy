"""
Historical Performance - Portfolio performance charts and analytics.
Professional trading UI with comprehensive performance tracking.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
import json

from database import DatabaseManager, init_database
from components.theme import apply_theme, page_header


def get_cumulative_pnl_data():
    """Calculate cumulative P&L over time from closed positions."""
    closed_positions = DatabaseManager.get_closed_positions(limit=500)

    if not closed_positions:
        return pd.DataFrame()

    # Build daily P&L data
    pnl_by_date = {}
    for pos in closed_positions:
        if pos.close_date:
            date_str = pos.close_date.strftime("%Y-%m-%d")

            # Calculate P&L for this trade
            if pos.status == 'EXPIRED':
                pnl = pos.premium_collected * pos.quantity * 100
            else:
                close_price = pos.close_price or 0
                pnl = (pos.premium_collected - close_price) * pos.quantity * 100

            pnl_by_date[date_str] = pnl_by_date.get(date_str, 0) + pnl

    if not pnl_by_date:
        return pd.DataFrame()

    # Convert to DataFrame and calculate cumulative
    df = pd.DataFrame([
        {"Date": k, "Daily P&L": v}
        for k, v in sorted(pnl_by_date.items())
    ])

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Cumulative P&L'] = df['Daily P&L'].cumsum()

    return df


def render_performance_metrics():
    """Render the top performance metrics."""
    realized_pnl = DatabaseManager.calculate_realized_pnl()
    stats = DatabaseManager.get_position_stats()
    pnl_data = DatabaseManager.get_pnl_by_period('all')

    total_pnl = realized_pnl['total_pnl']
    win_rate = pnl_data.get('win_rate', 0)
    wins = pnl_data.get('wins', 0)
    losses = pnl_data.get('losses', 0)
    trade_count = pnl_data.get('trade_count', 0)

    # Calculate average win/loss
    avg_win = 0
    avg_loss = 0
    if wins > 0 or losses > 0:
        pnl_by_symbol = DatabaseManager.get_pnl_by_underlying()
        # Simplified calculation - would need more detailed tracking
        if trade_count > 0:
            avg_trade = total_pnl / trade_count if trade_count > 0 else 0

    st.markdown(f'''
    <div class="ob-metrics-row">
        <div class="ob-metric-hero" style="grid-column: span 2;">
            <div class="ob-metric-label">Total Realized P&L</div>
            <div class="ob-metric-value {'profit' if total_pnl >= 0 else 'loss'}">
                {"+" if total_pnl >= 0 else ""}${total_pnl:,.2f}
            </div>
        </div>
        <div class="ob-metric">
            <div class="ob-metric-label">Win Rate</div>
            <div class="ob-metric-value">{win_rate:.1f}%</div>
        </div>
        <div class="ob-metric">
            <div class="ob-metric-label">Wins / Losses</div>
            <div class="ob-metric-value">{wins} / {losses}</div>
        </div>
        <div class="ob-metric">
            <div class="ob-metric-label">Total Trades</div>
            <div class="ob-metric-value">{trade_count}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_cumulative_chart():
    """Render the cumulative P&L chart."""
    st.markdown('''
    <div class="ob-chart-container">
        <div class="ob-chart-header">
            <h3 class="ob-chart-title">Cumulative P&L Growth</h3>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    df = get_cumulative_pnl_data()

    if df.empty:
        st.markdown('''
        <div style="text-align: center; padding: 80px 20px; color: var(--text-muted);">
            <p style="font-size: 3rem; margin-bottom: 12px;">📈</p>
            <p style="font-size: 1.1rem; margin-bottom: 8px;">No performance data yet</p>
            <p style="font-size: 0.9rem;">Close some trades to see your performance chart</p>
        </div>
        ''', unsafe_allow_html=True)
        return

    # Use Streamlit's native chart
    st.line_chart(
        df.set_index('Date')['Cumulative P&L'],
        use_container_width=True,
        height=350
    )

    # Show the data table below
    with st.expander("View Data"):
        st.dataframe(
            df[['Date', 'Daily P&L', 'Cumulative P&L']],
            column_config={
                "Date": st.column_config.DateColumn("Date"),
                "Daily P&L": st.column_config.NumberColumn("Daily P&L", format="$%.2f"),
                "Cumulative P&L": st.column_config.NumberColumn("Cumulative", format="$%.2f"),
            },
            hide_index=True,
            use_container_width=True
        )


def render_monthly_breakdown():
    """Render monthly P&L breakdown."""
    st.markdown('''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">Monthly Performance</h3>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    closed_positions = DatabaseManager.get_closed_positions(limit=500)

    if not closed_positions:
        st.info("No closed trades to analyze")
        return

    # Group by month
    monthly_data = {}
    for pos in closed_positions:
        if pos.close_date:
            month_key = pos.close_date.strftime("%Y-%m")

            if pos.status == 'EXPIRED':
                pnl = pos.premium_collected * pos.quantity * 100
            else:
                close_price = pos.close_price or 0
                pnl = (pos.premium_collected - close_price) * pos.quantity * 100

            if month_key not in monthly_data:
                monthly_data[month_key] = {'pnl': 0, 'trades': 0, 'wins': 0}

            monthly_data[month_key]['pnl'] += pnl
            monthly_data[month_key]['trades'] += 1
            if pnl > 0:
                monthly_data[month_key]['wins'] += 1

    if not monthly_data:
        st.info("No monthly data available")
        return

    # Display as cards
    months = sorted(monthly_data.keys(), reverse=True)[:12]  # Last 12 months

    cols = st.columns(4)
    for i, month in enumerate(months):
        data = monthly_data[month]
        pnl = data['pnl']
        win_rate = (data['wins'] / data['trades'] * 100) if data['trades'] > 0 else 0

        with cols[i % 4]:
            pnl_class = "profit" if pnl >= 0 else "loss"
            pnl_sign = "+" if pnl >= 0 else ""

            st.markdown(f'''
            <div style="background: var(--card); border-radius: 12px; padding: 16px; margin-bottom: 12px; text-align: center;">
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 8px;">{month}</div>
                <div style="font-size: 1.25rem; font-weight: 700;" class="text-{pnl_class}">
                    {pnl_sign}${pnl:,.0f}
                </div>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">
                    {data['trades']} trades | {win_rate:.0f}% win
                </div>
            </div>
            ''', unsafe_allow_html=True)


def render_risk_distribution():
    """Render risk distribution by underlying and strategy."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('''
        <div class="ob-card">
            <div class="ob-card-header">
                <h3 class="ob-card-title">Risk by Underlying</h3>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        positions = DatabaseManager.get_open_positions()
        if positions:
            by_underlying = {}
            total_premium = sum(p.premium_collected * p.quantity * 100 for p in positions)

            for p in positions:
                if p.underlying not in by_underlying:
                    by_underlying[p.underlying] = 0
                by_underlying[p.underlying] += p.premium_collected * p.quantity * 100

            # Sort by exposure
            sorted_underlyings = sorted(by_underlying.items(), key=lambda x: x[1], reverse=True)

            for symbol, exposure in sorted_underlyings[:8]:
                pct = (exposure / total_premium * 100) if total_premium > 0 else 0
                bar_width = min(pct, 100)

                st.markdown(f'''
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 500;">{symbol}</span>
                        <span style="color: var(--text-muted);">{pct:.1f}%</span>
                    </div>
                    <div style="background: var(--card); border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background: var(--primary); height: 100%; width: {bar_width}%; border-radius: 4px;"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.caption("No open positions")

    with col2:
        st.markdown('''
        <div class="ob-card">
            <div class="ob-card-header">
                <h3 class="ob-card-title">Risk by Strategy</h3>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        positions = DatabaseManager.get_open_positions()
        if positions:
            by_strategy = {}
            total_premium = sum(p.premium_collected * p.quantity * 100 for p in positions)

            for p in positions:
                strategy = p.strategy_type or "Other"
                if strategy not in by_strategy:
                    by_strategy[strategy] = 0
                by_strategy[strategy] += p.premium_collected * p.quantity * 100

            sorted_strategies = sorted(by_strategy.items(), key=lambda x: x[1], reverse=True)

            strategy_colors = {
                "CSP": "#3B82F6",
                "CC": "#10B981",
                "BULL_PUT": "#8B5CF6",
                "BEAR_CALL": "#F59E0B",
                "Other": "#64748B"
            }

            for strategy, exposure in sorted_strategies:
                pct = (exposure / total_premium * 100) if total_premium > 0 else 0
                bar_width = min(pct, 100)
                color = strategy_colors.get(strategy, "#64748B")

                st.markdown(f'''
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 500;">{strategy}</span>
                        <span style="color: var(--text-muted);">{pct:.1f}%</span>
                    </div>
                    <div style="background: var(--card); border-radius: 4px; height: 8px; overflow: hidden;">
                        <div style="background: {color}; height: 100%; width: {bar_width}%; border-radius: 4px;"></div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.caption("No open positions")


def render_trade_statistics():
    """Render detailed trade statistics."""
    st.markdown('''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">Trade Statistics</h3>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    closed_positions = DatabaseManager.get_closed_positions(limit=500)

    if not closed_positions:
        st.info("No closed trades to analyze")
        return

    # Calculate statistics
    pnls = []
    for pos in closed_positions:
        if pos.status == 'EXPIRED':
            pnl = pos.premium_collected * pos.quantity * 100
        else:
            close_price = pos.close_price or 0
            pnl = (pos.premium_collected - close_price) * pos.quantity * 100
        pnls.append(pnl)

    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    largest_win = max(wins) if wins else 0
    largest_loss = min(losses) if losses else 0
    profit_factor = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
    expectancy = sum(pnls) / len(pnls) if pnls else 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f'''
        <div style="background: var(--card); border-radius: 12px; padding: 16px;">
            <div style="margin-bottom: 16px;">
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Avg Win</div>
                <div style="font-size: 1.25rem; font-weight: 700;" class="text-profit">${avg_win:,.2f}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Avg Loss</div>
                <div style="font-size: 1.25rem; font-weight: 700;" class="text-loss">${abs(avg_loss):,.2f}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''
        <div style="background: var(--card); border-radius: 12px; padding: 16px;">
            <div style="margin-bottom: 16px;">
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Largest Win</div>
                <div style="font-size: 1.25rem; font-weight: 700;" class="text-profit">${largest_win:,.2f}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Largest Loss</div>
                <div style="font-size: 1.25rem; font-weight: 700;" class="text-loss">${abs(largest_loss):,.2f}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        pf_display = f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞"
        st.markdown(f'''
        <div style="background: var(--card); border-radius: 12px; padding: 16px;">
            <div style="margin-bottom: 16px;">
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Profit Factor</div>
                <div style="font-size: 1.25rem; font-weight: 700;">{pf_display}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;">Expectancy</div>
                <div style="font-size: 1.25rem; font-weight: 700;" class="{'text-profit' if expectancy >= 0 else 'text-loss'}">${expectancy:,.2f}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)


def render_performance_page():
    """Render the historical performance page."""
    # Apply theme
    apply_theme()

    # Initialize database
    init_database()

    # Page header
    st.markdown(page_header("Historical Performance", "Track your trading performance over time"), unsafe_allow_html=True)

    # Top metrics
    render_performance_metrics()

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    # Main chart
    render_cumulative_chart()

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    # Monthly breakdown
    render_monthly_breakdown()

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    # Risk distribution
    render_risk_distribution()

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    # Trade statistics
    render_trade_statistics()


# Run the page
render_performance_page()
