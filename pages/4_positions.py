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


def render_positions():
    """Render the positions page."""
    st.title("💼 Positions")
    st.markdown("Track and manage your options positions")

    # Initialize database
    init_database()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Open Positions", "➕ Add Position", "📜 History"])

    with tab1:
        render_open_positions()

    with tab2:
        render_add_position()

    with tab3:
        render_position_history()


def render_open_positions():
    """Render open positions grid."""
    st.subheader("Open Positions")

    positions = DatabaseManager.get_open_positions()

    if not positions:
        st.info("No open positions. Add a position using the 'Add Position' tab.")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    total_premium = sum(p.premium_collected * p.quantity * 100 for p in positions)
    avg_dte = sum(p.days_to_expiry for p in positions) / len(positions) if positions else 0

    with col1:
        st.metric("Open Positions", len(positions))
    with col2:
        st.metric("Total Premium", f"${total_premium:,.2f}")
    with col3:
        st.metric("Avg DTE", f"{avg_dte:.0f} days")
    with col4:
        expiring_soon = sum(1 for p in positions if p.days_to_expiry <= 7)
        st.metric("Expiring Soon", expiring_soon)

    st.markdown("---")

    # Position table
    for pos in positions:
        with st.expander(
            f"{'🔴' if pos.days_to_expiry <= 3 else '🟡' if pos.days_to_expiry <= 7 else '🟢'} "
            f"{pos.underlying} | ${pos.strike:.2f} {pos.option_type} | "
            f"Exp: {pos.expiry.strftime('%Y-%m-%d') if pos.expiry else 'N/A'} | "
            f"DTE: {pos.days_to_expiry}",
            expanded=pos.days_to_expiry <= 7
        ):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.write(f"**Strategy:** {pos.strategy_type}")
                st.write(f"**Quantity:** {pos.quantity}")

            with col2:
                st.write(f"**Premium:** ${pos.premium_collected:.2f}")
                st.write(f"**Total:** ${pos.premium_collected * pos.quantity * 100:.2f}")

            with col3:
                st.write(f"**Opened:** {pos.open_date.strftime('%Y-%m-%d') if pos.open_date else 'N/A'}")
                st.write(f"**Days to Expiry:** {pos.days_to_expiry}")

            with col4:
                if pos.notes:
                    st.write(f"**Notes:** {pos.notes}")

            # Action buttons
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("✅ Close", key=f"close_{pos.id}"):
                    st.session_state[f"closing_{pos.id}"] = True

            with col2:
                if st.button("🔄 Roll", key=f"roll_{pos.id}"):
                    st.info("Roll functionality coming soon!")

            with col3:
                if st.button("📝 Edit", key=f"edit_{pos.id}"):
                    st.session_state[f"editing_{pos.id}"] = True

            with col4:
                if st.button("🗑️ Delete", key=f"delete_{pos.id}"):
                    DatabaseManager.delete_position(pos.id)
                    st.success("Position deleted")
                    st.rerun()

            # Close position dialog
            if st.session_state.get(f"closing_{pos.id}"):
                st.markdown("---")
                st.markdown("### Close Position")
                close_price = st.number_input(
                    "Close Price",
                    value=0.0,
                    step=0.05,
                    key=f"close_price_{pos.id}"
                )
                close_status = st.selectbox(
                    "Status",
                    [STATUS_CLOSED, STATUS_ASSIGNED, STATUS_EXPIRED],
                    key=f"close_status_{pos.id}"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Confirm Close", key=f"confirm_close_{pos.id}"):
                        DatabaseManager.close_position(pos.id, close_price, close_status)
                        st.success("Position closed!")
                        del st.session_state[f"closing_{pos.id}"]
                        st.rerun()
                with col2:
                    if st.button("Cancel", key=f"cancel_close_{pos.id}"):
                        del st.session_state[f"closing_{pos.id}"]
                        st.rerun()


def render_add_position():
    """Render add position form."""
    st.subheader("Add New Position")

    with st.form("add_position_form"):
        col1, col2 = st.columns(2)

        with col1:
            underlying = st.text_input("Underlying Symbol").upper()
            option_type = st.selectbox("Option Type", [PUT, CALL])
            strike = st.number_input("Strike Price", value=100.0, step=1.0)
            expiry = st.date_input("Expiration Date", min_value=date.today())

        with col2:
            quantity = st.number_input("Quantity", value=1, min_value=1, step=1)
            premium = st.number_input("Premium Collected (per share)", value=1.0, step=0.05)
            strategy = st.selectbox(
                "Strategy",
                [STRATEGY_CSP, STRATEGY_CC, STRATEGY_BULL_PUT, STRATEGY_BEAR_CALL,
                 STRATEGY_IRON_CONDOR, STRATEGY_STRANGLE]
            )
            open_date = st.date_input("Open Date", value=date.today())

        notes = st.text_area("Notes (optional)")

        submitted = st.form_submit_button("Add Position", use_container_width=True)

        if submitted:
            if not underlying:
                st.error("Please enter a symbol")
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

                # Add opening trade
                trade = Trade(
                    position_id=position_id,
                    action="OPEN",
                    price=premium,
                    quantity=quantity,
                    trade_date=datetime.combine(open_date, datetime.min.time())
                )
                DatabaseManager.add_trade(trade)

                st.success(f"Position added! ID: {position_id}")
                st.balloons()

    # Quick add from IBKR (placeholder)
    st.markdown("---")
    st.subheader("Import from IBKR")

    if st.session_state.get('ibkr_connected', False):
        if st.button("🔄 Sync Positions from IBKR"):
            st.info("Syncing positions from IBKR...")
            # This would call ibkr_client.get_positions() and import
    else:
        st.info("Connect to IBKR in Settings to sync positions automatically.")


def render_position_history():
    """Render closed positions history."""
    st.subheader("Position History")

    positions = DatabaseManager.get_all_positions()
    closed_positions = [p for p in positions if p.status != STATUS_OPEN]

    if not closed_positions:
        st.info("No closed positions yet.")
        return

    # Summary
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

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Closed Positions", len(closed_positions))
    with col2:
        st.metric("Realized P/L", f"${total_realized:,.2f}")
    with col3:
        st.metric("Wins", wins)
    with col4:
        win_rate = (wins / len(closed_positions) * 100) if closed_positions else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")

    st.markdown("---")

    # History table
    history_data = []
    for pos in closed_positions:
        pnl = 0
        if pos.close_price is not None:
            pnl = (pos.premium_collected - pos.close_price) * pos.quantity * 100

        history_data.append({
            'Symbol': pos.underlying,
            'Type': pos.option_type,
            'Strike': f"${pos.strike:.2f}",
            'Strategy': pos.strategy_type,
            'Status': pos.status,
            'Premium': f"${pos.premium_collected:.2f}",
            'Close': f"${pos.close_price:.2f}" if pos.close_price else "-",
            'P/L': f"${pnl:.2f}",
            'Open Date': pos.open_date.strftime('%Y-%m-%d') if pos.open_date else 'N/A',
            'Close Date': pos.close_date.strftime('%Y-%m-%d') if pos.close_date else 'N/A'
        })

    df = pd.DataFrame(history_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


# Run the page
render_positions()
