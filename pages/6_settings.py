"""
Settings Page - Configuration and IBKR connection.
"""

import streamlit as st
from datetime import datetime

from database import DatabaseManager, init_database
from config.settings import get_settings, Settings, IBKRSettings
from data.ibkr_client import get_ibkr_client
from components.styles import apply_global_styles


def render_settings():
    """Render the settings page."""
    # Apply global styles
    apply_global_styles()

    # Compact header
    st.markdown("""
    <div style="margin-bottom: 0.75rem;">
        <h1 style="margin: 0; font-size: 1.75rem;">Settings</h1>
        <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9rem;">Configure Options Buddy</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize
    init_database()
    settings = get_settings()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["IBKR", "Watchlists", "Scanner", "Alerts"])

    with tab1:
        render_ibkr_settings(settings)

    with tab2:
        render_watchlist_settings()

    with tab3:
        render_scanner_defaults(settings)

    with tab4:
        render_alert_settings(settings)


def render_ibkr_settings(settings: Settings):
    """Render IBKR connection settings."""
    connected = st.session_state.get('ibkr_connected', False)
    active_client_id = st.session_state.get('ibkr_active_client_id', None)

    # Connection status banner
    if connected:
        connection_time = st.session_state.get('ibkr_connection_time', '')
        client_id_display = f" | Client ID: {active_client_id}" if active_client_id else ""
        st.markdown(f"""
        <div class="ob-banner-success">
            <strong>Connected to IBKR</strong>
            <span class="text-muted" style="margin-left: 12px;">Since: {connection_time}{client_id_display}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="ob-banner-error">
            <strong>Not Connected</strong>
            <span class="text-muted" style="margin-left: 12px;">Configure and connect below</span>
        </div>
        """, unsafe_allow_html=True)

    # Connection settings - compact
    st.markdown("#### Connection Settings")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        host = st.text_input("Host", value=settings.ibkr.host, help="Usually 127.0.0.1")

    with col2:
        port = st.number_input("Port", value=settings.ibkr.port, min_value=1000, max_value=65535,
                                help="7497=paper, 7496=live")

    with col3:
        client_id = st.number_input("Client ID", value=settings.ibkr.client_id, min_value=1, max_value=999,
                                     help="Will use random ID if conflict detected")

    with col4:
        market_data_type = st.selectbox(
            "Data Type",
            options=[1, 2, 3, 4],
            index=settings.ibkr.market_data_type - 1,
            format_func=lambda x: {1: "Live", 2: "Frozen", 3: "Delayed", 4: "Delayed Frozen"}[x]
        )

    # Connection buttons - now with 4 columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Connect", use_container_width=True, disabled=connected, type="primary"):
            with st.spinner("Connecting..."):
                try:
                    client = get_ibkr_client()
                    client.settings = IBKRSettings(
                        host=host, port=port, client_id=client_id, market_data_type=market_data_type
                    )
                    status = client.connect()

                    if status.is_connected:
                        st.session_state.ibkr_connected = True
                        st.session_state.ibkr_connection_time = datetime.now().strftime("%H:%M:%S")
                        st.session_state.ibkr_active_client_id = client._active_client_id
                        st.rerun()
                    else:
                        st.error(f"Failed: {status.error_message}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col2:
        if st.button("Disconnect", use_container_width=True, disabled=not connected):
            try:
                client = get_ibkr_client()
                client.disconnect()
                st.session_state.ibkr_connected = False
                st.session_state.ibkr_connection_time = None
                st.session_state.ibkr_active_client_id = None
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col3:
        if st.button("Force Reconnect", use_container_width=True,
                     help="Use when connection is stuck after app reload"):
            with st.spinner("Reconnecting..."):
                try:
                    client = get_ibkr_client()
                    client.settings = IBKRSettings(
                        host=host, port=port, client_id=client_id, market_data_type=market_data_type
                    )
                    status = client.force_reconnect()

                    if status.is_connected:
                        st.session_state.ibkr_connected = True
                        st.session_state.ibkr_connection_time = datetime.now().strftime("%H:%M:%S")
                        st.session_state.ibkr_active_client_id = client._active_client_id
                        st.success(f"Reconnected with client ID {client._active_client_id}")
                        st.rerun()
                    else:
                        st.error(f"Failed: {status.error_message}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col4:
        if st.button("Test", use_container_width=True):
            try:
                client = get_ibkr_client()
                status = client.get_status()
                if status.is_connected:
                    st.success(f"OK! Server v{status.server_version}")
                else:
                    st.warning("Not connected")
            except Exception as e:
                st.error(f"Failed: {str(e)}")

    # Setup guide - collapsed by default
    with st.expander("Setup Guide"):
        st.markdown("""
        **Prerequisites:**
        - IBKR account with options trading
        - TWS or IB Gateway installed

        **Quick Setup:**
        1. Open TWS/Gateway and log in
        2. Go to: Edit > Global Configuration > API > Settings
        3. Enable "ActiveX and Socket Clients"
        4. Set port: 7497 (paper) or 7496 (live)
        5. Click Connect above

        **Troubleshooting:**
        - Connection refused: Ensure TWS is running
        - Client ID in use: Use "Force Reconnect" button (uses random ID)
        - Stuck after code reload: Use "Force Reconnect" button
        - No data: Check market data subscriptions
        """)


def render_watchlist_settings():
    """Render watchlist management."""
    watchlists = DatabaseManager.get_all_watchlists()

    # Create new - compact
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        new_name = st.text_input("New Watchlist", placeholder="Name", label_visibility="collapsed")
    with col2:
        new_desc = st.text_input("Description", placeholder="Description (optional)", label_visibility="collapsed")
    with col3:
        if st.button("Create", use_container_width=True):
            if new_name:
                try:
                    DatabaseManager.create_watchlist(new_name, new_desc)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # Existing watchlists
    for wl in watchlists:
        with st.expander(f"{wl.name} ({len(wl.symbols)} symbols)"):
            st.caption(wl.description or "No description")

            # Show symbols as chips
            if wl.symbols:
                chips_html = " ".join([
                    f'<span class="ob-chip">{s}</span>'
                    for s in wl.symbols
                ])
                st.markdown(f'<div style="margin-bottom: 8px;">{chips_html}</div>', unsafe_allow_html=True)
            else:
                st.caption("No symbols")

            # Add symbol
            col1, col2 = st.columns([3, 1])
            with col1:
                new_symbol = st.text_input("Add", key=f"add_{wl.id}", placeholder="AAPL",
                                            label_visibility="collapsed").upper()
            with col2:
                if st.button("Add", key=f"add_btn_{wl.id}", use_container_width=True):
                    if new_symbol:
                        DatabaseManager.add_symbol_to_watchlist(wl.id, new_symbol)
                        st.rerun()

            # Remove symbols
            if wl.symbols:
                to_remove = st.multiselect("Remove", wl.symbols, key=f"remove_{wl.id}",
                                            label_visibility="collapsed")
                if to_remove and st.button("Remove Selected", key=f"remove_btn_{wl.id}"):
                    for sym in to_remove:
                        DatabaseManager.remove_symbol_from_watchlist(wl.id, sym)
                    st.rerun()

            # Delete
            if wl.name != "Default":
                if st.button("Delete Watchlist", key=f"delete_{wl.id}"):
                    DatabaseManager.delete_watchlist(wl.id)
                    st.rerun()


def render_scanner_defaults(settings: Settings):
    """Render scanner default settings."""
    st.caption("Pre-selected when you open Scanner")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**DTE Range**")
        min_dte = st.number_input("Min DTE", value=settings.scanner.min_dte, min_value=1, max_value=365)
        max_dte = st.number_input("Max DTE", value=settings.scanner.max_dte, min_value=1, max_value=365)

        st.markdown("**Delta Range**")
        min_delta = st.number_input("Min Delta", value=settings.scanner.min_delta,
                                     min_value=0.05, max_value=0.50, step=0.05)
        max_delta = st.number_input("Max Delta", value=settings.scanner.max_delta,
                                     min_value=0.05, max_value=0.50, step=0.05)

    with col2:
        st.markdown("**Premium & Volatility**")
        min_premium = st.number_input("Min Premium ($)", value=settings.scanner.min_premium,
                                       min_value=0.01, step=0.25)
        iv_hv_threshold = st.number_input("IV/HV Threshold", value=settings.scanner.iv_hv_threshold,
                                           min_value=1.0, max_value=3.0, step=0.1)

        st.markdown("**Strategies**")
        strategies = st.multiselect("Default", ["CSP", "CC", "BULL_PUT", "BEAR_CALL"],
                                     default=settings.scanner.strategies)

    if st.button("Save Scanner Defaults", use_container_width=True, type="primary"):
        DatabaseManager.set_setting("scanner_min_dte", str(min_dte))
        DatabaseManager.set_setting("scanner_max_dte", str(max_dte))
        DatabaseManager.set_setting("scanner_min_delta", str(min_delta))
        DatabaseManager.set_setting("scanner_max_delta", str(max_delta))
        DatabaseManager.set_setting("scanner_min_premium", str(min_premium))
        DatabaseManager.set_setting("scanner_iv_hv_threshold", str(iv_hv_threshold))
        DatabaseManager.set_setting("scanner_strategies", ",".join(strategies))
        st.success("Saved!")


def render_alert_settings(settings: Settings):
    """Render alert configuration."""
    st.caption("Configure position alerts")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Expiry Alerts**")
        expiry_warning = st.number_input("Days before expiry", value=settings.alerts.days_to_expiry_warning,
                                          min_value=1, max_value=30)

        st.markdown("**Delta Alerts**")
        delta_warning = st.number_input("Alert when delta >", value=settings.alerts.delta_warning_threshold,
                                         min_value=0.30, max_value=0.95, step=0.05)

    with col2:
        st.markdown("**Profit/Loss Targets**")
        profit_target = st.number_input("Profit target (%)", value=settings.alerts.profit_target_percent,
                                         min_value=10.0, max_value=100.0, step=5.0)
        loss_limit = st.number_input("Loss limit (%)", value=settings.alerts.loss_limit_percent,
                                      min_value=50.0, max_value=500.0, step=25.0)

    if st.button("Save Alert Settings", use_container_width=True, type="primary"):
        DatabaseManager.set_setting("alert_expiry_warning", str(expiry_warning))
        DatabaseManager.set_setting("alert_delta_warning", str(delta_warning))
        DatabaseManager.set_setting("alert_profit_target", str(profit_target))
        DatabaseManager.set_setting("alert_loss_limit", str(loss_limit))
        st.success("Saved!")

    # Risk-free rate
    st.markdown("---")
    st.markdown("**Calculation Settings**")

    risk_free = st.number_input("Risk-Free Rate (%)", value=settings.risk_free_rate * 100,
                                 min_value=0.0, max_value=20.0, step=0.25)

    if st.button("Save Calculation Settings"):
        DatabaseManager.set_setting("risk_free_rate", str(risk_free / 100))
        st.success("Saved!")


# Run the page
render_settings()
