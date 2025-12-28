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
        <div class="ob-empty-state">
            <p style="margin: 0;">No open positions. Use the 'Add Position' tab to get started.</p>
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

        # Determine urgency class and badge
        if dte <= 3:
            card_class = "ob-position-critical"
            badge_class = "ob-badge-critical"
            badge = "CRITICAL"
        elif dte <= 7:
            card_class = "ob-position-warning"
            badge_class = "ob-badge-warning"
            badge = "EXPIRING"
        else:
            card_class = "ob-position-normal"
            badge_class = None
            badge = None

        # Position card header
        badge_html = f'<span class="{badge_class}">{badge}</span>' if badge else ''
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.1rem; font-weight: 600;">{pos.underlying}</span>
                    <span class="text-muted" style="margin-left: 8px;">${pos.strike:.0f} {pos.option_type}</span>
                    <span class="text-muted" style="margin-left: 8px;">| {pos.strategy_type}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 0.85rem;">
                        <strong>{dte}d</strong> to {pos.expiry.strftime('%m/%d') if pos.expiry else 'N/A'}
                    </span>
                    {badge_html}
                </div>
            </div>
            <div style="display: flex; gap: 24px; margin-top: 8px; font-size: 0.85rem;" class="text-muted">
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
        <div class="ob-banner-success">
            <strong>IBKR Connected</strong>
            <span class="text-muted" style="margin-left: 12px;">Sync your live positions</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Sync Positions from IBKR", type="primary"):
            with st.spinner("Syncing..."):
                from data.ibkr_client import get_ibkr_client

                client = get_ibkr_client()
                ibkr_positions = client.get_positions()

                if ibkr_positions:
                    option_positions = [p for p in ibkr_positions if p.get('sec_type') == 'OPT']
                    stock_positions = [p for p in ibkr_positions if p.get('sec_type') == 'STK']

                    # Store in session state for import
                    st.session_state['ibkr_option_positions'] = option_positions
                    st.session_state['ibkr_stock_positions'] = stock_positions

                    if option_positions:
                        st.success(f"Found {len(option_positions)} option position(s)!")
                    else:
                        st.info("No option positions found in IBKR.")

                    if stock_positions:
                        st.info(f"Found {len(stock_positions)} stock position(s).")
                else:
                    st.session_state['ibkr_option_positions'] = []
                    st.session_state['ibkr_stock_positions'] = []
                    st.warning("No positions found.")

        # Display synced option positions with import functionality
        ibkr_options = st.session_state.get('ibkr_option_positions', [])
        if ibkr_options:
            st.markdown("#### Synced Option Positions")

            # Import all button
            col1, col2, col3 = st.columns([2, 2, 4])
            with col1:
                if st.button("Import All Options", type="primary", use_container_width=True):
                    st.session_state['import_all_options'] = True
            with col2:
                if st.button("Clear Synced", use_container_width=True):
                    st.session_state['ibkr_option_positions'] = []
                    st.session_state['ibkr_stock_positions'] = []
                    st.rerun()

            # Check if importing all
            if st.session_state.get('import_all_options'):
                st.markdown("##### Set Premium for All Positions")
                st.caption("IBKR doesn't provide premium collected. Enter the premium you received for each position.")

                import_data = {}
                for i, pos in enumerate(ibkr_options):
                    pos_key = f"{pos['symbol']}_{pos['strike']}_{pos['expiry']}_{pos['right']}"
                    col1, col2, col3 = st.columns([3, 2, 2])

                    with col1:
                        # Parse expiry
                        expiry_str = pos.get('expiry', '')
                        if len(expiry_str) == 8:
                            expiry_display = f"{expiry_str[:4]}-{expiry_str[4:6]}-{expiry_str[6:]}"
                        else:
                            expiry_display = expiry_str

                        qty = abs(pos.get('quantity', 1))
                        right = "CALL" if pos.get('right', '').upper() in ['C', 'CALL'] else "PUT"

                        st.markdown(f"""
                        <div style="padding: 8px 0; font-size: 0.9rem;">
                            <strong>{pos['symbol']}</strong> ${pos['strike']:.0f} {right}
                            <span style="opacity: 0.7;">| Exp: {expiry_display} | Qty: {qty}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        premium = st.number_input(
                            "Premium",
                            value=0.50,
                            min_value=0.01,
                            step=0.05,
                            key=f"import_premium_{i}",
                            label_visibility="collapsed"
                        )
                        import_data[i] = {'pos': pos, 'premium': premium}

                    with col3:
                        strategy = st.selectbox(
                            "Strategy",
                            [STRATEGY_CSP, STRATEGY_CC, STRATEGY_BULL_PUT, STRATEGY_BEAR_CALL],
                            key=f"import_strategy_{i}",
                            label_visibility="collapsed"
                        )
                        import_data[i]['strategy'] = strategy

                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("Confirm Import All", type="primary"):
                        imported_count = 0
                        for i, data in import_data.items():
                            pos = data['pos']
                            try:
                                # Parse position data
                                symbol = pos.get('symbol', '')
                                strike = float(pos.get('strike', 0))
                                right = pos.get('right', '').upper()
                                option_type = CALL if right in ['C', 'CALL'] else PUT
                                expiry_str = pos.get('expiry', '')
                                qty = int(abs(pos.get('quantity', 1)))

                                # Parse expiry date
                                if len(expiry_str) == 8:
                                    expiry_date = date(
                                        int(expiry_str[:4]),
                                        int(expiry_str[4:6]),
                                        int(expiry_str[6:])
                                    )
                                else:
                                    expiry_date = date.today()

                                # Create position
                                position = Position(
                                    underlying=symbol,
                                    option_type=option_type,
                                    strike=strike,
                                    expiry=expiry_date,
                                    quantity=qty,
                                    premium_collected=data['premium'],
                                    open_date=date.today(),
                                    strategy_type=data['strategy'],
                                    notes=f"Imported from IBKR"
                                )

                                position_id = DatabaseManager.add_position(position)

                                trade = Trade(
                                    position_id=position_id,
                                    action="OPEN",
                                    price=data['premium'],
                                    quantity=qty,
                                    trade_date=datetime.now()
                                )
                                DatabaseManager.add_trade(trade)
                                imported_count += 1

                            except Exception as e:
                                st.error(f"Error importing {pos.get('symbol', 'position')}: {e}")

                        if imported_count > 0:
                            st.success(f"Imported {imported_count} position(s)!")
                            st.session_state['ibkr_option_positions'] = []
                            st.session_state['import_all_options'] = False
                            st.balloons()
                            st.rerun()

                with col2:
                    if st.button("Cancel"):
                        st.session_state['import_all_options'] = False
                        st.rerun()

            else:
                # Show positions with individual import buttons
                for i, pos in enumerate(ibkr_options):
                    # Parse expiry
                    expiry_str = pos.get('expiry', '')
                    if len(expiry_str) == 8:
                        expiry_display = f"{expiry_str[:4]}-{expiry_str[4:6]}-{expiry_str[6:]}"
                    else:
                        expiry_display = expiry_str

                    qty = abs(pos.get('quantity', 1))
                    right = "CALL" if pos.get('right', '').upper() in ['C', 'CALL'] else "PUT"

                    col1, col2 = st.columns([5, 1])

                    with col1:
                        st.markdown(f"""
                        <div class="ob-synced-item">
                            <strong>{pos['symbol']}</strong> ${pos['strike']:.0f} {right}
                            <span class="text-muted">| Exp: {expiry_display} | Qty: {qty}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        if st.button("Import", key=f"import_single_{i}"):
                            st.session_state[f'importing_pos_{i}'] = True

                    # Individual import form
                    if st.session_state.get(f'importing_pos_{i}'):
                        with st.container():
                            st.markdown(f"##### Import {pos['symbol']} {right}")
                            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                            with col1:
                                single_premium = st.number_input(
                                    "Premium (per share)",
                                    value=0.50,
                                    min_value=0.01,
                                    step=0.05,
                                    key=f"single_premium_{i}"
                                )

                            with col2:
                                single_strategy = st.selectbox(
                                    "Strategy",
                                    [STRATEGY_CSP, STRATEGY_CC, STRATEGY_BULL_PUT, STRATEGY_BEAR_CALL],
                                    key=f"single_strategy_{i}"
                                )

                            with col3:
                                if st.button("Add", key=f"confirm_single_{i}", type="primary"):
                                    try:
                                        symbol = pos.get('symbol', '')
                                        strike = float(pos.get('strike', 0))
                                        option_type = CALL if right == "CALL" else PUT

                                        if len(expiry_str) == 8:
                                            expiry_date = date(
                                                int(expiry_str[:4]),
                                                int(expiry_str[4:6]),
                                                int(expiry_str[6:])
                                            )
                                        else:
                                            expiry_date = date.today()

                                        position = Position(
                                            underlying=symbol,
                                            option_type=option_type,
                                            strike=strike,
                                            expiry=expiry_date,
                                            quantity=qty,
                                            premium_collected=single_premium,
                                            open_date=date.today(),
                                            strategy_type=single_strategy,
                                            notes="Imported from IBKR"
                                        )

                                        position_id = DatabaseManager.add_position(position)

                                        trade = Trade(
                                            position_id=position_id,
                                            action="OPEN",
                                            price=single_premium,
                                            quantity=qty,
                                            trade_date=datetime.now()
                                        )
                                        DatabaseManager.add_trade(trade)

                                        # Remove from synced list
                                        ibkr_options.pop(i)
                                        st.session_state['ibkr_option_positions'] = ibkr_options
                                        del st.session_state[f'importing_pos_{i}']

                                        st.success(f"Imported {symbol}!")
                                        st.rerun()

                                    except Exception as e:
                                        st.error(f"Error: {e}")

                            with col4:
                                if st.button("Cancel", key=f"cancel_single_{i}"):
                                    del st.session_state[f'importing_pos_{i}']
                                    st.rerun()

            st.markdown("---")

        # Show stock positions if any
        ibkr_stocks = st.session_state.get('ibkr_stock_positions', [])
        if ibkr_stocks:
            with st.expander(f"Stock positions ({len(ibkr_stocks)})"):
                for pos in ibkr_stocks:
                    avg_cost = pos.get('avg_cost', 0)
                    st.write(f"**{pos['symbol']}**: {pos['quantity']} @ ${avg_cost:.2f}")
                st.caption("Stock positions shown for reference. Use them for covered call strategies.")

    else:
        st.markdown("""
        <div class="ob-banner-warning">
            <strong>Not Connected</strong>
            <span class="text-muted" style="margin-left: 12px;">Connect to IBKR to sync your live positions</span>
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
        <div class="ob-empty-state">
            <p style="margin: 0;">No closed positions yet.</p>
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
