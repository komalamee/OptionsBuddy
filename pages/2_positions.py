"""
Positions Tracker - Detailed view of all open and closed positions.
Professional trading UI with comprehensive P&L tracking.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import DatabaseManager, init_database
from components.theme import apply_theme, page_header, status_badge


def render_positions_metrics():
    """Render the top metrics for positions."""
    positions = DatabaseManager.get_open_positions()
    realized_pnl = DatabaseManager.calculate_realized_pnl()
    open_premium = DatabaseManager.calculate_open_premium()
    stats = DatabaseManager.get_position_stats()

    pnl_value = realized_pnl['total_pnl']
    win_rate = stats.get('win_rate', 0)
    total_trades = realized_pnl.get('closed_count', 0)

    st.markdown(f'''
    <div class="ob-metrics-row">
        <div class="ob-metric">
            <div class="ob-metric-label">Total P&L</div>
            <div class="ob-metric-value {'profit' if pnl_value >= 0 else 'loss'}">
                {"+" if pnl_value >= 0 else ""}${pnl_value:,.2f}
            </div>
        </div>
        <div class="ob-metric">
            <div class="ob-metric-label">Open Premium</div>
            <div class="ob-metric-value">${open_premium:,.2f}</div>
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


def render_open_positions():
    """Render the open positions table."""
    positions = DatabaseManager.get_open_positions()

    st.markdown('''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">Open Positions</h3>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if not positions:
        st.markdown('''
        <div style="text-align: center; padding: 60px 20px; color: var(--text-muted);">
            <p style="font-size: 3rem; margin-bottom: 12px;">📭</p>
            <p style="font-size: 1.1rem; margin-bottom: 8px;">No open positions</p>
            <p style="font-size: 0.9rem;">Use the Scanner to find new opportunities</p>
        </div>
        ''', unsafe_allow_html=True)
        return

    # Build position data
    position_data = []
    for pos in positions:
        dte = pos.days_to_expiry

        # Status based on DTE
        if dte <= 3:
            status = "CRITICAL"
            status_class = "loss"
        elif dte <= 7:
            status = "EXPIRING"
            status_class = "warning"
        else:
            status = "ACTIVE"
            status_class = "info"

        position_data.append({
            "id": pos.id,
            "Symbol": pos.underlying,
            "Type": pos.option_type,
            "Strike": pos.strike,
            "Expiry": pos.expiry.strftime("%Y-%m-%d") if pos.expiry else "-",
            "DTE": dte,
            "Qty": pos.quantity,
            "Premium": pos.premium_collected,
            "Strategy": pos.strategy_type,
            "Status": status,
            "status_class": status_class
        })

    # Render as styled table
    st.markdown('''
    <div class="ob-table-container">
        <table class="ob-table">
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Strike</th>
                    <th>Expiry</th>
                    <th>DTE</th>
                    <th>Qty</th>
                    <th>Premium</th>
                    <th>Strategy</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    ''', unsafe_allow_html=True)

    for pos in position_data:
        dte_color = "var(--loss)" if pos['DTE'] <= 3 else "var(--warning)" if pos['DTE'] <= 7 else "inherit"

        st.markdown(f'''
            <tr>
                <td><strong>{pos['Symbol']}</strong></td>
                <td><span class="ob-tag">{pos['Type']}</span></td>
                <td>${pos['Strike']:.0f}</td>
                <td>{pos['Expiry']}</td>
                <td style="color: {dte_color}; font-weight: 600;">{pos['DTE']}d</td>
                <td>{pos['Qty']}</td>
                <td>${pos['Premium']:.2f}</td>
                <td>{pos['Strategy']}</td>
                <td><span class="ob-badge ob-badge-{pos['status_class']}">{pos['Status']}</span></td>
                <td>
                    <button class="ob-btn ob-btn-ghost" style="padding: 4px 8px; font-size: 0.75rem;">Close</button>
                </td>
            </tr>
        ''', unsafe_allow_html=True)

    st.markdown('''
            </tbody>
        </table>
    </div>
    ''', unsafe_allow_html=True)

    # Also show as Streamlit dataframe for interactivity
    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    with st.expander("Interactive View", expanded=False):
        df = pd.DataFrame([{k: v for k, v in p.items() if k not in ['id', 'status_class']} for p in position_data])

        edited_df = st.data_editor(
            df,
            column_config={
                "Strike": st.column_config.NumberColumn("Strike", format="$%.0f"),
                "Premium": st.column_config.NumberColumn("Premium", format="$%.2f"),
                "DTE": st.column_config.NumberColumn("DTE", width="small"),
            },
            hide_index=True,
            use_container_width=True,
            disabled=True
        )


def render_closed_positions():
    """Render the closed positions history."""
    closed_positions = DatabaseManager.get_closed_positions(limit=50)

    st.markdown('''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">Trade History</h3>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if not closed_positions:
        st.markdown('''
        <div style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
            <p>No closed trades yet</p>
        </div>
        ''', unsafe_allow_html=True)
        return

    # Build trade data
    trade_data = []
    for pos in closed_positions:
        # Calculate P&L
        if pos.status == 'EXPIRED':
            pnl = pos.premium_collected * pos.quantity * 100
        else:
            close_price = pos.close_price or 0
            pnl = (pos.premium_collected - close_price) * pos.quantity * 100

        trade_data.append({
            "Close Date": pos.close_date.strftime("%Y-%m-%d") if pos.close_date else "-",
            "Symbol": pos.underlying,
            "Type": pos.option_type,
            "Strike": pos.strike,
            "Qty": pos.quantity,
            "Premium": pos.premium_collected,
            "Close $": pos.close_price or 0,
            "P&L": pnl,
            "Status": pos.status,
            "Strategy": pos.strategy_type
        })

    df = pd.DataFrame(trade_data)

    st.dataframe(
        df,
        column_config={
            "Strike": st.column_config.NumberColumn("Strike", format="$%.0f"),
            "Premium": st.column_config.NumberColumn("Premium", format="$%.2f"),
            "Close $": st.column_config.NumberColumn("Close $", format="$%.2f"),
            "P&L": st.column_config.NumberColumn("P&L", format="$%.2f"),
        },
        hide_index=True,
        use_container_width=True,
        height=min(400, 50 + len(trade_data) * 35)
    )


def render_pnl_breakdown():
    """Render P&L breakdown by symbol and strategy."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('''
        <div class="ob-card">
            <div class="ob-card-header">
                <h3 class="ob-card-title">P&L by Symbol</h3>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        pnl_by_symbol = DatabaseManager.get_pnl_by_underlying()
        if pnl_by_symbol:
            for item in pnl_by_symbol[:8]:
                pnl_class = "text-profit" if item['pnl'] >= 0 else "text-loss"
                pnl_sign = "+" if item['pnl'] >= 0 else ""
                st.markdown(f'''
                <div style="display: flex; justify-content: space-between; padding: 10px 14px; background: var(--card); border-radius: 8px; margin-bottom: 6px;">
                    <div>
                        <span style="font-weight: 600;">{item['underlying']}</span>
                        <span style="color: var(--text-muted); margin-left: 8px; font-size: 0.85rem;">{item['trade_count']} trades</span>
                    </div>
                    <span class="{pnl_class}" style="font-weight: 600;">{pnl_sign}${item['pnl']:,.2f}</span>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.caption("No closed trades")

    with col2:
        st.markdown('''
        <div class="ob-card">
            <div class="ob-card-header">
                <h3 class="ob-card-title">P&L by Strategy</h3>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        pnl_by_strategy = DatabaseManager.get_pnl_by_strategy()
        if pnl_by_strategy:
            for item in pnl_by_strategy:
                pnl_class = "text-profit" if item['pnl'] >= 0 else "text-loss"
                pnl_sign = "+" if item['pnl'] >= 0 else ""
                st.markdown(f'''
                <div style="display: flex; justify-content: space-between; padding: 10px 14px; background: var(--card); border-radius: 8px; margin-bottom: 6px;">
                    <div>
                        <span style="font-weight: 600;">{item['strategy_type']}</span>
                        <span style="color: var(--text-muted); margin-left: 8px; font-size: 0.85rem;">{item['win_rate']:.0f}% win</span>
                    </div>
                    <span class="{pnl_class}" style="font-weight: 600;">{pnl_sign}${item['pnl']:,.2f}</span>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.caption("No closed trades")


def render_position_actions():
    """Render position management actions."""
    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    with st.expander("Position Management"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Close Position")
            positions = DatabaseManager.get_open_positions()

            if positions:
                position_options = {
                    f"{p.underlying} ${p.strike} {p.option_type} ({p.days_to_expiry}d)": p.id
                    for p in positions
                }

                selected = st.selectbox("Select Position", list(position_options.keys()))
                close_price = st.number_input("Close Price", min_value=0.0, step=0.05, format="%.2f")
                close_status = st.selectbox("Status", ["CLOSED", "EXPIRED", "ASSIGNED", "ROLLED"])

                if st.button("Close Position", type="primary"):
                    pos_id = position_options[selected]
                    DatabaseManager.close_position(
                        pos_id,
                        close_price=close_price,
                        status=close_status,
                        close_date=date.today()
                    )
                    st.success("Position closed!")
                    st.rerun()
            else:
                st.info("No open positions to close")

        with col2:
            st.markdown("##### Add Position")
            with st.form("add_position"):
                symbol = st.text_input("Symbol", placeholder="AAPL").upper()
                col_a, col_b = st.columns(2)
                with col_a:
                    option_type = st.selectbox("Type", ["PUT", "CALL"])
                with col_b:
                    strike = st.number_input("Strike", min_value=0.0, step=1.0)

                col_c, col_d = st.columns(2)
                with col_c:
                    expiry = st.date_input("Expiry", value=date.today() + timedelta(days=30))
                with col_d:
                    quantity = st.number_input("Quantity", min_value=1, value=1)

                premium = st.number_input("Premium", min_value=0.0, step=0.05, format="%.2f")
                strategy = st.selectbox("Strategy", ["CSP", "CC", "BULL_PUT", "BEAR_CALL", "OTHER"])

                if st.form_submit_button("Add Position", type="primary"):
                    if symbol and strike > 0 and premium > 0:
                        from database.models import Position
                        new_pos = Position(
                            underlying=symbol,
                            option_type=option_type,
                            strike=strike,
                            expiry=expiry,
                            quantity=quantity,
                            premium_collected=premium,
                            open_date=date.today(),
                            status="OPEN",
                            strategy_type=strategy
                        )
                        DatabaseManager.add_position(new_pos)
                        st.success(f"Added {symbol} position!")
                        st.rerun()
                    else:
                        st.error("Please fill all required fields")


def render_positions_page():
    """Render the positions tracker page."""
    # Apply theme
    apply_theme()

    # Initialize database
    init_database()

    # Page header
    st.markdown(page_header("Positions Tracker", "Track and manage all your options positions"), unsafe_allow_html=True)

    # Top metrics
    render_positions_metrics()

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    # Tabs for different views
    tab_open, tab_closed, tab_breakdown = st.tabs(["Open Positions", "Trade History", "P&L Breakdown"])

    with tab_open:
        render_open_positions()
        render_position_actions()

    with tab_closed:
        render_closed_positions()

    with tab_breakdown:
        render_pnl_breakdown()


# Run the page
render_positions_page()
