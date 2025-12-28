"""
Scanner Page - Daily opportunity scanner for mispriced options.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime

from database import DatabaseManager, init_database
from config.constants import CALL, PUT, DEFAULT_MIN_DTE, DEFAULT_MAX_DTE


def render_scanner():
    """Render the scanner page."""
    st.title("🔍 Option Scanner")
    st.markdown("Find mispriced options for premium selling")

    # Initialize database
    init_database()

    # Check connection status
    connected = st.session_state.get('ibkr_connected', False)

    if not connected:
        st.warning("⚠️ Not connected to IBKR. Go to Settings to connect.")
        st.info("You can still configure your scan parameters below. Connect to IBKR to fetch live data.")

    # Sidebar filters
    st.sidebar.subheader("📋 Scan Filters")

    # Watchlist selection
    watchlists = DatabaseManager.get_all_watchlists()
    watchlist_names = [w.name for w in watchlists] if watchlists else ["Default"]
    selected_watchlist = st.sidebar.selectbox(
        "Watchlist",
        watchlist_names,
        help="Select which watchlist to scan"
    )

    # Get symbols from selected watchlist
    selected_wl = next((w for w in watchlists if w.name == selected_watchlist), None)
    symbols = selected_wl.symbols if selected_wl else []

    # DTE range
    st.sidebar.markdown("### DTE Range")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_dte = st.number_input("Min DTE", value=7, min_value=1, max_value=365)
    with col2:
        max_dte = st.number_input("Max DTE", value=45, min_value=1, max_value=365)

    # Delta range
    st.sidebar.markdown("### Delta Range")
    delta_range = st.sidebar.slider(
        "Delta (absolute)",
        min_value=0.05,
        max_value=0.50,
        value=(0.15, 0.35),
        step=0.05,
        help="Filter options by delta. Lower delta = further OTM"
    )

    # Strategy type
    strategy_types = st.sidebar.multiselect(
        "Strategy Types",
        ["Cash-Secured Put", "Covered Call", "Bull Put Spread", "Bear Call Spread"],
        default=["Cash-Secured Put"],
        help="Select strategies to scan for"
    )

    # Option type based on strategy
    if "Cash-Secured Put" in strategy_types or "Bull Put Spread" in strategy_types:
        include_puts = True
    else:
        include_puts = False

    if "Covered Call" in strategy_types or "Bear Call Spread" in strategy_types:
        include_calls = True
    else:
        include_calls = False

    # Minimum premium
    min_premium = st.sidebar.number_input(
        "Min Premium ($)",
        value=0.50,
        min_value=0.01,
        step=0.25,
        help="Minimum bid price"
    )

    # IV/HV threshold
    iv_hv_threshold = st.sidebar.slider(
        "IV/HV Ratio Minimum",
        min_value=1.0,
        max_value=2.0,
        value=1.2,
        step=0.1,
        help="Minimum IV to HV ratio. Higher = more overpriced"
    )

    st.sidebar.markdown("---")

    # Main content area
    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.subheader("Watchlist Symbols")

        if symbols:
            # Display as chips
            symbol_text = " | ".join([f"**{s}**" for s in symbols])
            st.markdown(symbol_text)
        else:
            st.info("No symbols in this watchlist. Add symbols in Settings.")

        # Quick add symbol
        with st.expander("Quick Add Symbol"):
            new_symbol = st.text_input("Symbol", placeholder="AAPL").upper()
            if st.button("Add to Watchlist") and new_symbol:
                if selected_wl:
                    DatabaseManager.add_symbol_to_watchlist(selected_wl.id, new_symbol)
                    st.success(f"Added {new_symbol} to {selected_watchlist}")
                    st.rerun()

    with col_right:
        st.subheader("Scan")
        scan_button = st.button(
            "🚀 Run Scan",
            use_container_width=True,
            disabled=not connected or not symbols
        )

    st.markdown("---")

    # Results section
    st.subheader("📊 Scan Results")

    if scan_button and connected and symbols:
        with st.spinner("Scanning options..."):
            # This would call the actual scanner
            # For now, show placeholder
            st.info("Scanning feature requires IBKR connection. Results will appear here.")

            # Placeholder results
            results_placeholder = pd.DataFrame({
                'Symbol': ['AAPL', 'MSFT', 'NVDA'],
                'Type': ['PUT', 'PUT', 'PUT'],
                'Strike': [180, 400, 120],
                'Expiry': ['2024-02-16', '2024-02-16', '2024-02-16'],
                'DTE': [21, 21, 21],
                'Bid': [2.45, 3.80, 4.20],
                'IV': [0.28, 0.25, 0.42],
                'HV': [0.22, 0.21, 0.35],
                'IV/HV': [1.27, 1.19, 1.20],
                'Delta': [-0.25, -0.22, -0.28],
                'Score': [78, 65, 72]
            })

            st.dataframe(
                results_placeholder,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Score': st.column_config.ProgressColumn(
                        'Score',
                        min_value=0,
                        max_value=100,
                        format="%d"
                    ),
                    'Bid': st.column_config.NumberColumn(format="$%.2f"),
                    'Strike': st.column_config.NumberColumn(format="$%.0f"),
                    'IV': st.column_config.NumberColumn(format="%.1f%%"),
                    'HV': st.column_config.NumberColumn(format="%.1f%%"),
                }
            )

    elif not connected:
        st.info("Connect to IBKR in Settings to scan for live opportunities.")

        # Show example of what results look like
        with st.expander("Preview: What results look like"):
            example_df = pd.DataFrame({
                'Symbol': ['AAPL', 'MSFT'],
                'Type': ['PUT', 'PUT'],
                'Strike': [180, 400],
                'Expiry': ['2024-02-16', '2024-02-16'],
                'DTE': [21, 21],
                'Bid': [2.45, 3.80],
                'IV/HV': [1.27, 1.19],
                'Delta': [-0.25, -0.22],
                'Score': [78, 65]
            })
            st.dataframe(example_df, use_container_width=True, hide_index=True)

    elif not symbols:
        st.info("Add symbols to your watchlist to start scanning.")

    # Current filter summary
    st.markdown("---")
    st.caption(
        f"**Current Filters:** DTE {min_dte}-{max_dte} | "
        f"Delta {delta_range[0]:.2f}-{delta_range[1]:.2f} | "
        f"Min Premium ${min_premium:.2f} | "
        f"IV/HV > {iv_hv_threshold:.1f}"
    )


# Run the page
render_scanner()
