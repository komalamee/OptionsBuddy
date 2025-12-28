"""
Settings Page - Configuration and IBKR connection.
"""

import streamlit as st
from datetime import datetime

from database import DatabaseManager, init_database
from config.settings import get_settings, Settings, IBKRSettings
from data.ibkr_client import get_ibkr_client


def render_settings():
    """Render the settings page."""
    st.title("⚙️ Settings")
    st.markdown("Configure Options Buddy")

    # Initialize
    init_database()
    settings = get_settings()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔗 IBKR Connection",
        "📋 Watchlists",
        "🎯 Scanner Defaults",
        "⚠️ Alerts"
    ])

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
    st.subheader("Interactive Brokers Connection")

    # Current status
    connected = st.session_state.get('ibkr_connected', False)

    if connected:
        st.success("🟢 Connected to IBKR")
        connection_time = st.session_state.get('ibkr_connection_time')
        if connection_time:
            st.caption(f"Connected since: {connection_time}")
    else:
        st.warning("🔴 Not connected to IBKR")

    st.markdown("---")

    # Connection settings
    st.markdown("### Connection Settings")

    col1, col2 = st.columns(2)

    with col1:
        host = st.text_input(
            "Host",
            value=settings.ibkr.host,
            help="Usually 127.0.0.1 for local TWS/Gateway"
        )

        port = st.number_input(
            "Port",
            value=settings.ibkr.port,
            min_value=1000,
            max_value=65535,
            help="7497 for paper trading, 7496 for live"
        )

    with col2:
        client_id = st.number_input(
            "Client ID",
            value=settings.ibkr.client_id,
            min_value=1,
            max_value=999,
            help="Unique ID for this connection"
        )

        market_data_type = st.selectbox(
            "Market Data Type",
            options=[1, 2, 3, 4],
            index=settings.ibkr.market_data_type - 1,
            format_func=lambda x: {
                1: "1 - Live",
                2: "2 - Frozen",
                3: "3 - Delayed",
                4: "4 - Delayed Frozen"
            }[x],
            help="Type of market data to request"
        )

    st.markdown("---")

    # Connection buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔌 Connect", use_container_width=True, disabled=connected):
            with st.spinner("Connecting to IBKR..."):
                try:
                    client = get_ibkr_client()
                    client.settings = IBKRSettings(
                        host=host,
                        port=port,
                        client_id=client_id,
                        market_data_type=market_data_type
                    )
                    status = client.connect()

                    if status.is_connected:
                        st.session_state.ibkr_connected = True
                        st.session_state.ibkr_connection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.success("Connected successfully!")
                        st.rerun()
                    else:
                        st.error(f"Connection failed: {status.error_message}")

                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    with col2:
        if st.button("🔌 Disconnect", use_container_width=True, disabled=not connected):
            try:
                client = get_ibkr_client()
                client.disconnect()
                st.session_state.ibkr_connected = False
                st.session_state.ibkr_connection_time = None
                st.success("Disconnected")
                st.rerun()
            except Exception as e:
                st.error(f"Disconnect error: {str(e)}")

    with col3:
        if st.button("🔄 Test Connection", use_container_width=True):
            try:
                client = get_ibkr_client()
                status = client.get_status()
                if status.is_connected:
                    st.success(f"Connection OK! Server version: {status.server_version}")
                else:
                    st.warning("Not connected")
            except Exception as e:
                st.error(f"Test failed: {str(e)}")

    # Setup guide
    with st.expander("📖 IBKR Setup Guide"):
        st.markdown("""
        ### How to Connect to Interactive Brokers

        **Prerequisites:**
        1. Active IBKR account with options trading permissions
        2. TWS (Trader Workstation) or IB Gateway installed
        3. Paper trading account recommended for testing

        **Setup Steps:**

        1. **Download TWS or IB Gateway**
           - Visit: [IBKR Trading Platforms](https://www.interactivebrokers.com/en/trading/ib-api.php)
           - IB Gateway is lighter weight (recommended for API-only use)

        2. **Enable API Access**
           - Open TWS/Gateway and log in
           - Go to: Edit > Global Configuration > API > Settings
           - Enable: "Enable ActiveX and Socket Clients"
           - Set Socket Port: 7497 (paper) or 7496 (live)
           - Disable: "Read-Only API" if you want trading access later

        3. **Configure Trusted IPs**
           - Add 127.0.0.1 to trusted IPs for local connections

        4. **Market Data Subscriptions**
           - Ensure you have options data enabled for your symbols
           - For paper trading, you may need delayed data

        **Troubleshooting:**

        | Issue | Solution |
        |-------|----------|
        | Connection refused | Ensure TWS/Gateway is running |
        | Port mismatch | Check port in TWS matches settings |
        | No market data | Check data subscriptions |
        | Frozen data only | Normal outside market hours |
        """)


def render_watchlist_settings():
    """Render watchlist management."""
    st.subheader("Watchlist Management")

    watchlists = DatabaseManager.get_all_watchlists()

    # Create new watchlist
    with st.expander("➕ Create New Watchlist"):
        col1, col2 = st.columns([2, 1])
        with col1:
            new_name = st.text_input("Watchlist Name", placeholder="My Watchlist")
            new_desc = st.text_input("Description (optional)", placeholder="Tech stocks I'm watching")
        with col2:
            if st.button("Create", use_container_width=True):
                if new_name:
                    try:
                        DatabaseManager.create_watchlist(new_name, new_desc)
                        st.success(f"Created watchlist: {new_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Please enter a name")

    st.markdown("---")

    # Manage existing watchlists
    for wl in watchlists:
        with st.expander(f"📋 {wl.name} ({len(wl.symbols)} symbols)"):
            st.caption(wl.description or "No description")

            # Show symbols
            if wl.symbols:
                st.markdown("**Symbols:** " + ", ".join(wl.symbols))
            else:
                st.info("No symbols in this watchlist")

            # Add symbol
            col1, col2 = st.columns([3, 1])
            with col1:
                new_symbol = st.text_input(
                    "Add Symbol",
                    key=f"add_{wl.id}",
                    placeholder="AAPL"
                ).upper()
            with col2:
                if st.button("Add", key=f"add_btn_{wl.id}", use_container_width=True):
                    if new_symbol:
                        DatabaseManager.add_symbol_to_watchlist(wl.id, new_symbol)
                        st.success(f"Added {new_symbol}")
                        st.rerun()

            # Remove symbols
            if wl.symbols:
                to_remove = st.multiselect(
                    "Remove Symbols",
                    wl.symbols,
                    key=f"remove_{wl.id}"
                )
                if to_remove and st.button("Remove Selected", key=f"remove_btn_{wl.id}"):
                    for sym in to_remove:
                        DatabaseManager.remove_symbol_from_watchlist(wl.id, sym)
                    st.success(f"Removed {len(to_remove)} symbols")
                    st.rerun()

            # Delete watchlist
            st.markdown("---")
            if wl.name != "Default":
                if st.button(f"🗑️ Delete Watchlist", key=f"delete_{wl.id}"):
                    DatabaseManager.delete_watchlist(wl.id)
                    st.success(f"Deleted {wl.name}")
                    st.rerun()
            else:
                st.caption("Default watchlist cannot be deleted")


def render_scanner_defaults(settings: Settings):
    """Render scanner default settings."""
    st.subheader("Scanner Defaults")

    st.info("These defaults will be pre-selected when you open the Scanner page.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### DTE Range")
        min_dte = st.number_input(
            "Minimum DTE",
            value=settings.scanner.min_dte,
            min_value=1,
            max_value=365
        )
        max_dte = st.number_input(
            "Maximum DTE",
            value=settings.scanner.max_dte,
            min_value=1,
            max_value=365
        )

        st.markdown("### Delta Range")
        min_delta = st.number_input(
            "Minimum Delta",
            value=settings.scanner.min_delta,
            min_value=0.05,
            max_value=0.50,
            step=0.05
        )
        max_delta = st.number_input(
            "Maximum Delta",
            value=settings.scanner.max_delta,
            min_value=0.05,
            max_value=0.50,
            step=0.05
        )

    with col2:
        st.markdown("### Premium & Volatility")
        min_premium = st.number_input(
            "Minimum Premium ($)",
            value=settings.scanner.min_premium,
            min_value=0.01,
            step=0.25
        )

        iv_hv_threshold = st.number_input(
            "IV/HV Ratio Threshold",
            value=settings.scanner.iv_hv_threshold,
            min_value=1.0,
            max_value=3.0,
            step=0.1
        )

        st.markdown("### Default Strategies")
        strategies = st.multiselect(
            "Strategies to Scan",
            ["CSP", "CC", "BULL_PUT", "BEAR_CALL"],
            default=settings.scanner.strategies
        )

    if st.button("💾 Save Scanner Defaults", use_container_width=True):
        # Save to database settings table
        DatabaseManager.set_setting("scanner_min_dte", str(min_dte))
        DatabaseManager.set_setting("scanner_max_dte", str(max_dte))
        DatabaseManager.set_setting("scanner_min_delta", str(min_delta))
        DatabaseManager.set_setting("scanner_max_delta", str(max_delta))
        DatabaseManager.set_setting("scanner_min_premium", str(min_premium))
        DatabaseManager.set_setting("scanner_iv_hv_threshold", str(iv_hv_threshold))
        DatabaseManager.set_setting("scanner_strategies", ",".join(strategies))
        st.success("Scanner defaults saved!")


def render_alert_settings(settings: Settings):
    """Render alert configuration."""
    st.subheader("Alert Settings")

    st.info("Configure when you want to be alerted about your positions.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Expiry Alerts")
        expiry_warning = st.number_input(
            "Days before expiry to warn",
            value=settings.alerts.days_to_expiry_warning,
            min_value=1,
            max_value=30
        )

        st.markdown("### Delta Alerts")
        delta_warning = st.number_input(
            "Alert when delta exceeds",
            value=settings.alerts.delta_warning_threshold,
            min_value=0.30,
            max_value=0.95,
            step=0.05
        )

    with col2:
        st.markdown("### Profit/Loss Targets")
        profit_target = st.number_input(
            "Profit target (%)",
            value=settings.alerts.profit_target_percent,
            min_value=10.0,
            max_value=100.0,
            step=5.0,
            help="Alert when option has lost this % of value"
        )

        loss_limit = st.number_input(
            "Loss limit (%)",
            value=settings.alerts.loss_limit_percent,
            min_value=50.0,
            max_value=500.0,
            step=25.0,
            help="Alert when loss reaches this % of premium"
        )

    if st.button("💾 Save Alert Settings", use_container_width=True):
        DatabaseManager.set_setting("alert_expiry_warning", str(expiry_warning))
        DatabaseManager.set_setting("alert_delta_warning", str(delta_warning))
        DatabaseManager.set_setting("alert_profit_target", str(profit_target))
        DatabaseManager.set_setting("alert_loss_limit", str(loss_limit))
        st.success("Alert settings saved!")

    # Risk-free rate
    st.markdown("---")
    st.subheader("Calculation Settings")

    risk_free = st.number_input(
        "Risk-Free Rate (%)",
        value=settings.risk_free_rate * 100,
        min_value=0.0,
        max_value=20.0,
        step=0.25,
        help="Used in Black-Scholes calculations"
    )

    if st.button("💾 Save Calculation Settings"):
        DatabaseManager.set_setting("risk_free_rate", str(risk_free / 100))
        st.success("Calculation settings saved!")


# Run the page
render_settings()
