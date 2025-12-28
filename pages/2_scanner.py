"""
Scanner Page - Daily opportunity scanner for mispriced options.
"""

import streamlit as st
import pandas as pd
import json
from datetime import date, datetime

from database import DatabaseManager, init_database
from config.constants import CALL, PUT, DEFAULT_MIN_DTE, DEFAULT_MAX_DTE
from components.styles import apply_global_styles


def load_filter_presets():
    """Load saved filter presets from database."""
    presets_json = DatabaseManager.get_setting("scanner_presets")
    if presets_json:
        try:
            return json.loads(presets_json)
        except:
            pass
    return {}


def save_filter_presets(presets):
    """Save filter presets to database."""
    DatabaseManager.set_setting("scanner_presets", json.dumps(presets))


def get_default_preset():
    """Get the default preset name."""
    return DatabaseManager.get_setting("scanner_default_preset") or ""


def set_default_preset(preset_name):
    """Set a preset as the default."""
    DatabaseManager.set_setting("scanner_default_preset", preset_name)


def render_scanner():
    """Render the scanner page."""
    # Apply global styles
    apply_global_styles()

    # Compact header
    st.markdown("""
    <div style="margin-bottom: 0.75rem;">
        <h1 style="margin: 0; font-size: 1.75rem;">Option Scanner</h1>
        <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9rem;">Find mispriced options for premium selling</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize database
    init_database()

    # Load presets
    presets = load_filter_presets()
    default_preset = get_default_preset()

    # Initialize session state for filters if not set
    if 'scanner_filters_loaded' not in st.session_state:
        st.session_state.scanner_filters_loaded = False

    # Load default preset on first load
    if not st.session_state.scanner_filters_loaded and default_preset and default_preset in presets:
        preset = presets[default_preset]
        st.session_state.min_dte = preset.get('min_dte', 7)
        st.session_state.max_dte = preset.get('max_dte', 45)
        st.session_state.delta_min = preset.get('delta_min', 0.15)
        st.session_state.delta_max = preset.get('delta_max', 0.35)
        st.session_state.min_premium = preset.get('min_premium', 0.50)
        st.session_state.iv_hv_threshold = preset.get('iv_hv_threshold', 1.2)
        st.session_state.strategies = preset.get('strategies', ["Naked Put"])
        st.session_state.scanner_filters_loaded = True

    # Check connection status
    connected = st.session_state.get('ibkr_connected', False)

    # Connection status in compact banner
    if not connected:
        st.markdown("""
        <div style="
            background: rgba(255, 165, 2, 0.15);
            border-left: 3px solid #ffa502;
            border-radius: 0 6px 6px 0;
            padding: 10px 16px;
            margin-bottom: 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <span>Not connected to IBKR. Configure scan parameters below, then connect to fetch live data.</span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([4, 1, 4])
        with col2:
            if st.button("Go to Settings", key="goto_settings_top"):
                st.switch_page("pages/6_settings.py")

    # Sidebar filters - more compact
    st.sidebar.markdown("### Scan Filters")

    # Preset selector - compact
    preset_names = list(presets.keys())
    if preset_names:
        preset_options = ["-- Select --"] + preset_names
        selected_preset = st.sidebar.selectbox(
            "Load Preset",
            preset_options,
            index=0,
            label_visibility="collapsed"
        )

        if selected_preset != "-- Select --" and selected_preset in presets:
            if st.sidebar.button("Apply", use_container_width=True, key="apply_preset"):
                preset = presets[selected_preset]
                st.session_state.min_dte = preset.get('min_dte', 7)
                st.session_state.max_dte = preset.get('max_dte', 45)
                st.session_state.delta_min = preset.get('delta_min', 0.15)
                st.session_state.delta_max = preset.get('delta_max', 0.35)
                st.session_state.min_premium = preset.get('min_premium', 0.50)
                st.session_state.iv_hv_threshold = preset.get('iv_hv_threshold', 1.2)
                st.session_state.strategies = preset.get('strategies', ["Naked Put"])
                st.rerun()

        if default_preset:
            st.sidebar.caption(f"Default: {default_preset}")

    st.sidebar.markdown("---")

    # Get watchlists for later use (but don't show selector here)
    watchlists = DatabaseManager.get_all_watchlists()
    watchlist_names = [w.name for w in watchlists] if watchlists else []

    # Initialize selected watchlist in session state
    if 'selected_watchlist' not in st.session_state:
        st.session_state.selected_watchlist = watchlist_names[0] if watchlist_names else None

    # Get symbols from selected watchlist
    selected_wl = next((w for w in watchlists if w.name == st.session_state.selected_watchlist), None)
    symbols = selected_wl.symbols if selected_wl else []

    # DTE range - inline
    st.sidebar.markdown("**DTE Range**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_dte = st.number_input("Min", value=st.session_state.get('min_dte', 7),
                                   min_value=1, max_value=365, key="input_min_dte",
                                   label_visibility="collapsed")
    with col2:
        max_dte = st.number_input("Max", value=st.session_state.get('max_dte', 45),
                                   min_value=1, max_value=365, key="input_max_dte",
                                   label_visibility="collapsed")
    st.sidebar.caption(f"{min_dte} - {max_dte} days")

    # Delta range
    st.sidebar.markdown("**Delta**")
    delta_range = st.sidebar.slider(
        "Delta",
        min_value=0.05, max_value=0.50,
        value=(st.session_state.get('delta_min', 0.15), st.session_state.get('delta_max', 0.35)),
        step=0.05, key="input_delta_range", label_visibility="collapsed"
    )

    # Strategy type - compact
    all_strategies = ["Naked Put", "Cash-Secured Put", "Naked Call", "Covered Call",
                      "Bull Put Spread", "Bear Call Spread", "Iron Condor", "Strangle"]
    strategy_types = st.sidebar.multiselect(
        "Strategies",
        all_strategies,
        default=st.session_state.get('strategies', ["Naked Put"]),
        key="input_strategies"
    )

    put_strategies = ["Naked Put", "Cash-Secured Put", "Bull Put Spread", "Iron Condor", "Strangle"]
    call_strategies = ["Naked Call", "Covered Call", "Bear Call Spread", "Iron Condor", "Strangle"]
    include_puts = any(s in strategy_types for s in put_strategies)
    include_calls = any(s in strategy_types for s in call_strategies)

    # Premium and IV/HV - inline
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_premium = st.number_input("Min Premium", value=st.session_state.get('min_premium', 0.50),
                                       min_value=0.01, step=0.25, key="input_min_premium")
    with col2:
        iv_hv_threshold = st.number_input("IV/HV >", value=st.session_state.get('iv_hv_threshold', 1.2),
                                           min_value=1.0, max_value=2.0, step=0.1, key="input_iv_hv")

    st.sidebar.markdown("---")

    # Save preset - compact
    with st.sidebar.expander("Save Preset"):
        new_preset_name = st.text_input("Name", placeholder="My Scan", key="new_preset_name")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save", use_container_width=True):
                if new_preset_name:
                    current_filters = {
                        'min_dte': min_dte, 'max_dte': max_dte,
                        'delta_min': delta_range[0], 'delta_max': delta_range[1],
                        'min_premium': min_premium, 'iv_hv_threshold': iv_hv_threshold,
                        'strategies': strategy_types
                    }
                    presets[new_preset_name] = current_filters
                    save_filter_presets(presets)
                    st.rerun()
        with col2:
            if st.button("Set Default", use_container_width=True):
                if new_preset_name:
                    current_filters = {
                        'min_dte': min_dte, 'max_dte': max_dte,
                        'delta_min': delta_range[0], 'delta_max': delta_range[1],
                        'min_premium': min_premium, 'iv_hv_threshold': iv_hv_threshold,
                        'strategies': strategy_types
                    }
                    presets[new_preset_name] = current_filters
                    save_filter_presets(presets)
                    set_default_preset(new_preset_name)
                    st.rerun()

    # Delete preset - compact
    if preset_names:
        with st.sidebar.expander("Delete Preset"):
            preset_to_delete = st.selectbox("Select", ["--"] + preset_names, key="delete_preset")
            if preset_to_delete != "--":
                if st.button("Delete", use_container_width=True):
                    del presets[preset_to_delete]
                    save_filter_presets(presets)
                    if default_preset == preset_to_delete:
                        set_default_preset("")
                    st.rerun()

    # Main content - Unified Watchlist & Symbol Selection
    # Clear section header showing what will be scanned
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(55, 66, 250, 0.1) 0%, rgba(55, 66, 250, 0.05) 100%);
        border: 1px solid rgba(55, 66, 250, 0.2);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 1rem;
    ">
        <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.7; margin-bottom: 8px;">
            Symbols to Scan
        </div>
    """, unsafe_allow_html=True)

    # Watchlist selector and symbols in one unified area
    col1, col2, col3, col4 = st.columns([2, 3, 2, 1])

    with col1:
        # Watchlist dropdown
        if watchlist_names:
            current_index = watchlist_names.index(st.session_state.selected_watchlist) if st.session_state.selected_watchlist in watchlist_names else 0
            selected_watchlist = st.selectbox(
                "Watchlist",
                watchlist_names,
                index=current_index,
                key="watchlist_selector",
                label_visibility="collapsed"
            )
            # Update session state and refresh symbols if changed
            if selected_watchlist != st.session_state.selected_watchlist:
                st.session_state.selected_watchlist = selected_watchlist
                st.rerun()
        else:
            st.caption("No watchlists")

    with col2:
        # Quick add symbol
        new_symbol = st.text_input("Add symbol", placeholder="Enter ticker (e.g. AAPL)", key="quick_add",
                                    label_visibility="collapsed")

    with col3:
        st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)
        if st.button("Add to List", use_container_width=True, key="add_symbol_btn"):
            if new_symbol and selected_wl:
                DatabaseManager.add_symbol_to_watchlist(selected_wl.id, new_symbol.upper().strip())
                st.rerun()

    with col4:
        st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)
        symbol_count = len(symbols) if symbols else 0
        st.markdown(f"<div style='text-align: center; padding: 8px; background: rgba(55, 66, 250, 0.2); border-radius: 8px; font-weight: 600;'>{symbol_count}</div>", unsafe_allow_html=True)

    # Display symbols as chips with remove buttons
    if symbols:
        # Create chips with delete capability
        chips_html = ""
        for sym in symbols:
            chips_html += f'''
            <span style="
                background: rgba(55, 66, 250, 0.15);
                border: 1px solid rgba(55, 66, 250, 0.3);
                padding: 6px 14px;
                border-radius: 20px;
                margin: 4px;
                font-size: 0.9rem;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            ">{sym}</span>
            '''
        st.markdown(f'''
        <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
            {chips_html}
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 20px; opacity: 0.6; margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
            No symbols in this watchlist. Add tickers above or manage watchlists in Settings.
        </div>
        """, unsafe_allow_html=True)

    # Close the container
    st.markdown("</div>", unsafe_allow_html=True)

    # Scan button - prominent, below the unified selection area
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        button_text = "Run Scan" if connected else "Connect to IBKR First"
        if symbols:
            button_text = f"Scan {len(symbols)} Symbols" if connected else "Connect to IBKR First"

        scan_button = st.button(
            button_text,
            use_container_width=True,
            disabled=not connected or not symbols,
            type="primary"
        )

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # Results section
    st.markdown("#### Scan Results")

    if scan_button and connected and symbols:
        with st.spinner("Scanning options..."):
            from data.ibkr_client import get_ibkr_client
            from data.historical_data import HistoricalDataFetcher
            from core.scoring import OpportunityScorer

            client = get_ibkr_client()
            fetcher = HistoricalDataFetcher()
            scorer = OpportunityScorer()

            results = []
            progress_bar = st.progress(0)

            for i, sym in enumerate(symbols):
                progress_bar.progress((i + 1) / len(symbols))

                try:
                    price = client.get_stock_price(sym)
                    if not price:
                        continue

                    expirations = client.get_option_chain_expirations(sym)
                    if not expirations:
                        continue

                    for exp in expirations[:5]:
                        try:
                            exp_date = datetime.strptime(exp, "%Y%m%d")
                            dte = (exp_date.date() - date.today()).days
                            if min_dte <= dte <= max_dte:
                                strikes = client.get_option_chain_strikes(sym, exp)
                                st.write(f"Found {len(strikes)} strikes for {sym} exp {exp}")
                        except:
                            continue

                except Exception as e:
                    st.warning(f"Error scanning {sym}: {str(e)}")

            progress_bar.empty()

            if results:
                df = pd.DataFrame(results)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Score': st.column_config.ProgressColumn('Score', min_value=0, max_value=100, format="%d"),
                        'Bid': st.column_config.NumberColumn(format="$%.2f"),
                        'Strike': st.column_config.NumberColumn(format="$%.0f"),
                    }
                )
            else:
                st.info("Scan complete. No opportunities found. Try adjusting filters.")

    elif not connected:
        st.markdown("""
        <div style="
            background: rgba(128, 128, 128, 0.1);
            border: 1px dashed rgba(128, 128, 128, 0.3);
            border-radius: 8px;
            padding: 40px;
            text-align: center;
        ">
            <p style="opacity: 0.7; margin: 0;">Connect to IBKR to scan for live opportunities</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("Go to Settings", key="goto_settings_results"):
                st.switch_page("pages/6_settings.py")

    elif not symbols:
        st.info("Add symbols to your watchlist to start scanning.")

    # Current filter summary - compact footer with watchlist reference
    watchlist_display = st.session_state.selected_watchlist or "None"
    symbol_count = len(symbols) if symbols else 0
    st.markdown(f"""
    <div style="
        margin-top: 1rem;
        padding: 10px 14px;
        background: rgba(128, 128, 128, 0.1);
        border-radius: 8px;
        font-size: 0.8rem;
        opacity: 0.8;
        display: flex;
        justify-content: space-between;
        align-items: center;
    ">
        <span><strong>{watchlist_display}</strong> ({symbol_count} symbols)</span>
        <span>DTE {min_dte}-{max_dte} | Delta {delta_range[0]:.2f}-{delta_range[1]:.2f} | Min ${min_premium:.2f} | IV/HV > {iv_hv_threshold:.1f}</span>
    </div>
    """, unsafe_allow_html=True)


# Run the page
render_scanner()
