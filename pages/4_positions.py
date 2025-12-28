"""
Positions Page - Track and manage options positions.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime

from database import DatabaseManager, init_database
from database.models import Position, Trade
from config.constants import (
    CALL, PUT,
    STATUS_OPEN, STATUS_CLOSED, STATUS_ASSIGNED, STATUS_EXPIRED, STATUS_ROLLED,
    STRATEGY_CSP, STRATEGY_CC, STRATEGY_BULL_PUT, STRATEGY_BEAR_CALL,
    STRATEGY_IRON_CONDOR, STRATEGY_STRANGLE
)
from components.styles import apply_global_styles, COLORS


def render_positions():
    """Render the positions page."""
    # Apply global styles
    apply_global_styles()

    # Compact header
    st.markdown("""
    <div style="margin-bottom: 0.75rem;">
        <h1 style="margin: 0; font-size: 1.75rem;">Positions</h1>
        <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9rem;">Track and manage your options positions</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize database
    init_database()

    # Tabs - compact styling
    tab1, tab2, tab3 = st.tabs(["Open Positions", "Add Position", "History"])

    with tab1:
        render_open_positions()

    with tab2:
        render_add_position()

    with tab3:
        render_position_history()


def render_open_positions():
    """Render open positions grid."""
    positions = DatabaseManager.get_open_positions()

    if not positions:
        st.markdown("""
        <div style="
            background: rgba(128, 128, 128, 0.1);
            border: 1px dashed rgba(128, 128, 128, 0.3);
            border-radius: 8px;
            padding: 40px;
            text-align: center;
        ">
            <p style="opacity: 0.7; margin: 0;">No open positions. Use the 'Add Position' tab to get started.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Summary metrics - compact row
    total_premium = sum(p.premium_collected * p.quantity * 100 for p in positions)
    avg_dte = sum(p.days_to_expiry for p in positions) / len(positions) if positions else 0
    expiring_soon = sum(1 for p in positions if p.days_to_expiry <= 7)
    expiring_critical = sum(1 for p in positions if p.days_to_expiry <= 3)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Open", len(positions))
    with col2:
        st.metric("Premium", f"${total_premium:,.0f}")
    with col3:
        st.metric("Avg DTE", f"{avg_dte:.0f}d")
    with col4:
        st.metric("Expiring", expiring_soon, delta="critical" if expiring_critical else None,
                  delta_color="inverse" if expiring_critical else "off")
    with col5:
        # Calculate unrealized P/L placeholder (would need current prices)
        st.metric("Unrealized", "$--")

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # Position cards - compact layout
    for pos in positions:
        dte = pos.days_to_expiry

        # Determine urgency colors
        if dte <= 3:
            border_color = "#ff4757"
            bg_color = "rgba(255, 71, 87, 0.1)"
            badge = "CRITICAL"
        elif dte <= 7:
            border_color = "#ffa502"
            bg_color = "rgba(255, 165, 2, 0.1)"
            badge = "EXPIRING"
        else:
            border_color = "rgba(128, 128, 128, 0.3)"
            bg_color = "rgba(128, 128, 128, 0.05)"
            badge = None

        # Position card header
        st.markdown(f"""
        <div style="
            background: {bg_color};
            border-left: 3px solid {border_color};
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin-bottom: 8px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.1rem; font-weight: 600;">{pos.underlying}</span>
                    <span style="opacity: 0.8; margin-left: 8px;">${pos.strike:.0f} {pos.option_type}</span>
                    <span style="opacity: 0.6; margin-left: 8px;">| {pos.strategy_type}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 0.85rem;">
                        <strong>{dte}d</strong> to {pos.expiry.strftime('%m/%d') if pos.expiry else 'N/A'}
                    </span>
                    {f'<span style="background: {border_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600;">{badge}</span>' if badge else ''}
                </div>
            </div>
            <div style="display: flex; gap: 24px; margin-top: 8px; font-size: 0.85rem; opacity: 0.9;">
                <span>Qty: {pos.quantity}</span>
                <span>Premium: ${pos.premium_collected:.2f}</span>
                <span>Total: ${pos.premium_collected * pos.quantity * 100:.0f}</span>
                <span>Opened: {pos.open_date.strftime('%m/%d') if pos.open_date else 'N/A'}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action buttons - compact inline
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 4])

        with col1:
            if st.button("Close", key=f"close_{pos.id}"):
                st.session_state[f"closing_{pos.id}"] = True

        with col2:
            if st.button("Roll", key=f"roll_{pos.id}"):
                st.info("Roll functionality coming soon!")

        with col3:
            if st.button("Edit", key=f"edit_{pos.id}"):
                st.session_state[f"editing_{pos.id}"] = True

        with col4:
            if st.button("Delete", key=f"delete_{pos.id}"):
                DatabaseManager.delete_position(pos.id)
                st.rerun()

        # Close position dialog - inline
        if st.session_state.get(f"closing_{pos.id}"):
            with st.container():
                st.markdown("##### Close Position")
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                with col1:
                    close_price = st.number_input("Close Price", value=0.0, step=0.05,
                                                   key=f"close_price_{pos.id}")
                with col2:
                    close_status = st.selectbox("Status",
                                                 [STATUS_CLOSED, STATUS_ASSIGNED, STATUS_EXPIRED],
                                                 key=f"close_status_{pos.id}")
                with col3:
                    if st.button("Confirm", key=f"confirm_close_{pos.id}", type="primary"):
                        DatabaseManager.close_position(pos.id, close_price, close_status)
                        del st.session_state[f"closing_{pos.id}"]
                        st.rerun()
                with col4:
                    if st.button("Cancel", key=f"cancel_close_{pos.id}"):
                        del st.session_state[f"closing_{pos.id}"]
                        st.rerun()

        st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)


def render_add_position():
    """Render add position form."""
    connected = st.session_state.get('ibkr_connected', False)

    # IBKR Import - Compact banner
    if connected:
        st.markdown("""
        <div style="
            background: rgba(46, 213, 115, 0.15);
            border-left: 3px solid #2ed573;
            border-radius: 0 6px 6px 0;
            padding: 12px 16px;
            margin-bottom: 1rem;
        ">
            <strong>IBKR Connected</strong> - Sync your live positions
        </div>
        """, unsafe_allow_html=True)

        if st.button("Sync Positions from IBKR", type="primary"):
            with st.spinner("Syncing..."):
                from data.ibkr_client import get_ibkr_client

                client = get_ibkr_client()
                ibkr_positions = client.get_positions()

                if ibkr_positions:
                    option_positions = [p for p in ibkr_positions if p.get('sec_type') == 'OPT']

                    if option_positions:
                        st.write(f"**{len(option_positions)} option position(s) found:**")
                        for pos in option_positions:
                            st.markdown(f"""
                            <div style="
                                background: rgba(55, 66, 250, 0.1);
                                border-radius: 6px;
                                padding: 8px 12px;
                                margin-bottom: 4px;
                                font-size: 0.9rem;
                            ">
                                <strong>{pos['symbol']}</strong> {pos['right']} ${pos['strike']}
                                | Exp: {pos['expiry']} | Qty: {pos['quantity']}
                            </div>
                            """, unsafe_allow_html=True)
                        st.caption("Add these positions manually below with your premium details.")
                    else:
                        st.info("No option positions found in IBKR.")

                    stock_positions = [p for p in ibkr_positions if p.get('sec_type') == 'STK']
                    if stock_positions:
                        with st.expander(f"Stock positions ({len(stock_positions)})"):
                            for pos in stock_positions:
                                st.write(f"**{pos['symbol']}**: {pos['quantity']} @ ${pos['avg_cost']:.2f}")
                else:
                    st.warning("No positions found.")
    else:
        st.markdown("""
        <div style="
            background: rgba(255, 165, 2, 0.15);
            border-left: 3px solid #ffa502;
            border-radius: 0 6px 6px 0;
            padding: 12px 16px;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <span>Connect to IBKR to sync your live positions</span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([4, 1, 4])
        with col2:
            if st.button("Settings", key="goto_settings_positions"):
                st.switch_page("pages/6_settings.py")

    st.markdown("#### Add Position Manually")

    # Compact form layout
    with st.form("add_position_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            underlying = st.text_input("Symbol").upper()
            strike = st.number_input("Strike", value=100.0, step=1.0)
            premium = st.number_input("Premium (per share)", value=1.0, step=0.05)

        with col2:
            option_type = st.selectbox("Type", [PUT, CALL])
            expiry = st.date_input("Expiration", min_value=date.today())
            quantity = st.number_input("Quantity", value=1, min_value=1, step=1)

        with col3:
            strategy = st.selectbox("Strategy",
                                     [STRATEGY_CSP, STRATEGY_CC, STRATEGY_BULL_PUT, STRATEGY_BEAR_CALL,
                                      STRATEGY_IRON_CONDOR, STRATEGY_STRANGLE])
            open_date = st.date_input("Open Date", value=date.today())

        notes = st.text_input("Notes (optional)")

        submitted = st.form_submit_button("Add Position", use_container_width=True, type="primary")

        if submitted:
            if not underlying:
                st.error("Enter a symbol")
            else:
                position = Position(
                    underlying=underlying,
                    option_type=option_type,
                    strike=strike,
                    expiry=expiry,
                    quantity=quantity,
                    premium_collected=premium,
                    open_date=open_date,
                    strategy_type=strategy,
                    notes=notes if notes else None
                )

                position_id = DatabaseManager.add_position(position)

                trade = Trade(
                    position_id=position_id,
                    action="OPEN",
                    price=premium,
                    quantity=quantity,
                    trade_date=datetime.combine(open_date, datetime.min.time())
                )
                DatabaseManager.add_trade(trade)

                st.success(f"Position added!")
                st.balloons()


def render_position_history():
    """Render closed positions history."""
    positions = DatabaseManager.get_all_positions()
    closed_positions = [p for p in positions if p.status != STATUS_OPEN]

    if not closed_positions:
        st.markdown("""
        <div style="
            background: rgba(128, 128, 128, 0.1);
            border: 1px dashed rgba(128, 128, 128, 0.3);
            border-radius: 8px;
            padding: 40px;
            text-align: center;
        ">
            <p style="opacity: 0.7; margin: 0;">No closed positions yet.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Calculate stats
    total_realized = 0
    wins = 0
    losses = 0

    for pos in closed_positions:
        if pos.close_price is not None:
            pnl = (pos.premium_collected - pos.close_price) * pos.quantity * 100
            total_realized += pnl
            if pnl > 0:
                wins += 1
            else:
                losses += 1

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Closed", len(closed_positions))
    with col2:
        color = "normal" if total_realized >= 0 else "inverse"
        st.metric("Realized P/L", f"${total_realized:,.0f}",
                  delta=f"+${total_realized:.0f}" if total_realized > 0 else f"${total_realized:.0f}",
                  delta_color=color)
    with col3:
        st.metric("Wins/Losses", f"{wins}/{losses}")
    with col4:
        win_rate = (wins / len(closed_positions) * 100) if closed_positions else 0
        st.metric("Win Rate", f"{win_rate:.0f}%")

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # History table with styled P/L
    history_data = []
    for pos in closed_positions:
        pnl = 0
        if pos.close_price is not None:
            pnl = (pos.premium_collected - pos.close_price) * pos.quantity * 100

        history_data.append({
            'Symbol': pos.underlying,
            'Type': pos.option_type,
            'Strike': pos.strike,
            'Strategy': pos.strategy_type,
            'Status': pos.status,
            'Premium': pos.premium_collected,
            'Close': pos.close_price if pos.close_price else 0,
            'P/L': pnl,
            'Open': pos.open_date.strftime('%m/%d') if pos.open_date else '-',
            'Closed': pos.close_date.strftime('%m/%d') if pos.close_date else '-'
        })

    df = pd.DataFrame(history_data)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Strike': st.column_config.NumberColumn("Strike", format="$%.0f"),
            'Premium': st.column_config.NumberColumn("Premium", format="$%.2f"),
            'Close': st.column_config.NumberColumn("Close", format="$%.2f"),
            'P/L': st.column_config.NumberColumn("P/L", format="$%.0f"),
        }
    )


# Run the page
render_positions()
