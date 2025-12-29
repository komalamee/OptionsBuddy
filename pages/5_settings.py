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
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["IBKR", "AI Assistant", "Watchlists", "Scanner", "Alerts", "Profile"])

    with tab1:
        render_ibkr_settings(settings)

    with tab2:
        render_ai_settings()

    with tab3:
        render_watchlist_settings()

    with tab4:
        render_scanner_defaults(settings)

    with tab5:
        render_alert_settings(settings)

    with tab6:
        render_profile_settings()


def render_ai_settings():
    """Render AI Assistant settings - multi-provider API key and model configuration."""

    # Provider definitions with their models and API info
    PROVIDERS = {
        "openai": {
            "name": "OpenAI",
            "key_prefix": "sk-",
            "key_setting": "openai_api_key",
            "base_url": None,  # Uses default
            "get_key_url": "https://platform.openai.com/api-keys",
            "models": {
                "gpt-4o-mini": "Fast & affordable - good for most queries",
                "gpt-4o": "Most capable - better reasoning",
                "o1-mini": "Reasoning model - good for complex analysis",
                "o1": "Advanced reasoning - best for deep calculations",
            }
        },
        "deepseek": {
            "name": "DeepSeek",
            "key_prefix": "sk-",
            "key_setting": "deepseek_api_key",
            "base_url": "https://api.deepseek.com",
            "get_key_url": "https://platform.deepseek.com/api_keys",
            "models": {
                "deepseek-chat": "Fast general chat model",
                "deepseek-reasoner": "Deep thinking - best for complex calculations",
            }
        },
        "anthropic": {
            "name": "Anthropic (Claude)",
            "key_prefix": "sk-ant-",
            "key_setting": "anthropic_api_key",
            "base_url": "https://api.anthropic.com",
            "get_key_url": "https://console.anthropic.com/settings/keys",
            "models": {
                "claude-3-5-sonnet-20241022": "Best balance of speed & capability",
                "claude-3-5-haiku-20241022": "Fastest - good for quick queries",
                "claude-3-opus-20240229": "Most capable - complex analysis",
            }
        },
        "groq": {
            "name": "Groq (Fast)",
            "key_prefix": "gsk_",
            "key_setting": "groq_api_key",
            "base_url": "https://api.groq.com/openai/v1",
            "get_key_url": "https://console.groq.com/keys",
            "models": {
                "llama-3.3-70b-versatile": "Fast Llama 3.3 70B",
                "llama-3.1-8b-instant": "Ultra-fast Llama 3.1 8B",
                "mixtral-8x7b-32768": "Mixtral 8x7B - good reasoning",
            }
        }
    }

    # Get active provider
    active_provider = DatabaseManager.get_setting("ai_provider") or "openai"

    # Status banner - show active provider and key status
    provider_config = PROVIDERS.get(active_provider, PROVIDERS["openai"])
    saved_key = DatabaseManager.get_setting(provider_config["key_setting"])
    has_key = bool(saved_key and len(saved_key) > 10)

    if has_key:
        masked_key = saved_key[:8] + "..." + saved_key[-4:] if len(saved_key) > 12 else "***"
        st.markdown(f"""
        <div class="ob-banner-success">
            <strong>{provider_config['name']} Configured</strong>
            <span class="text-muted" style="margin-left: 12px;">Key: {masked_key}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ob-banner-warning">
            <strong>{provider_config['name']} - API Key Required</strong>
            <span class="text-muted" style="margin-left: 12px;">Add your API key below</span>
        </div>
        """, unsafe_allow_html=True)

    # Provider selection
    st.markdown("#### AI Provider")

    provider_names = list(PROVIDERS.keys())
    provider_display = {k: v["name"] for k, v in PROVIDERS.items()}

    selected_provider = st.selectbox(
        "Provider",
        provider_names,
        index=provider_names.index(active_provider) if active_provider in provider_names else 0,
        format_func=lambda x: provider_display.get(x, x),
        label_visibility="collapsed"
    )

    if selected_provider != active_provider:
        DatabaseManager.set_setting("ai_provider", selected_provider)
        st.rerun()

    # Get current provider config
    provider_config = PROVIDERS[selected_provider]
    saved_key = DatabaseManager.get_setting(provider_config["key_setting"])
    has_key = bool(saved_key and len(saved_key) > 10)

    # API Key input
    st.markdown(f"#### {provider_config['name']} API Key")
    st.caption(f"Get your key from: {provider_config['get_key_url']}")

    col1, col2 = st.columns([3, 1])

    with col1:
        new_key = st.text_input(
            "API Key",
            type="password",
            placeholder=f"{provider_config['key_prefix']}...",
            label_visibility="collapsed"
        )

    with col2:
        if st.button("Save Key", use_container_width=True, type="primary"):
            if new_key:
                DatabaseManager.set_setting(provider_config["key_setting"], new_key)
                st.success("API key saved!")
                st.rerun()
            else:
                st.error("Please enter an API key")

    if has_key:
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Test Key", use_container_width=True):
                with st.spinner("Testing..."):
                    try:
                        if selected_provider == "anthropic":
                            import anthropic
                            client = anthropic.Anthropic(api_key=saved_key)
                            response = client.messages.create(
                                model="claude-3-5-haiku-20241022",
                                max_tokens=10,
                                messages=[{"role": "user", "content": "Say OK"}]
                            )
                            st.success("API key is valid!")
                        else:
                            # OpenAI-compatible API (OpenAI, DeepSeek, Groq)
                            import openai
                            client_kwargs = {"api_key": saved_key}
                            if provider_config["base_url"]:
                                client_kwargs["base_url"] = provider_config["base_url"]
                            client = openai.OpenAI(**client_kwargs)

                            # Use first model in provider's list
                            test_model = list(provider_config["models"].keys())[0]
                            response = client.chat.completions.create(
                                model=test_model,
                                messages=[{"role": "user", "content": "Say OK"}],
                                max_tokens=10
                            )
                            st.success("API key is valid!")
                    except Exception as e:
                        st.error(f"Invalid key: {str(e)[:100]}")

        with col2:
            if st.button("Remove Key", use_container_width=True):
                DatabaseManager.set_setting(provider_config["key_setting"], "")
                st.rerun()

    # Model selection
    st.markdown("---")
    st.markdown("#### Model Settings")

    saved_model = DatabaseManager.get_setting("ai_model") or list(provider_config["models"].keys())[0]
    models = list(provider_config["models"].keys())
    model_descriptions = provider_config["models"]

    # Ensure saved model is in current provider's list
    if saved_model not in models:
        saved_model = models[0]

    selected_model = st.selectbox(
        "Model",
        models,
        index=models.index(saved_model) if saved_model in models else 0,
        format_func=lambda x: f"{x} - {model_descriptions.get(x, '')}",
        help=f"Choose which {provider_config['name']} model to use"
    )

    if selected_model != saved_model:
        DatabaseManager.set_setting("ai_model", selected_model)
        st.success(f"Model set to {selected_model}")

    # Show thinking models recommendation
    if selected_provider == "deepseek":
        st.info("💡 **Tip:** `deepseek-reasoner` is excellent for complex options calculations, Greeks analysis, and strategy evaluation.")
    elif selected_provider == "openai" and "o1" in selected_model:
        st.info("💡 **Tip:** o1 models use chain-of-thought reasoning. They may take longer but provide deeper analysis.")

    # System prompt customization
    st.markdown("---")
    st.markdown("#### System Prompt")
    st.caption("Customize how the AI assistant behaves. It will automatically have context about your positions.")

    default_prompt = """You are an expert options trading assistant for Options Buddy. You help analyze positions, suggest strategies, and provide actionable recommendations.

Key behaviors:
- Be concise and direct
- Focus on premium selling strategies (CSP, covered calls, spreads)
- Consider risk management and position sizing
- When discussing specific positions, reference the user's actual data
- Explain your reasoning for recommendations
- Never recommend naked short calls without proper context"""

    saved_prompt = DatabaseManager.get_setting("ai_system_prompt") or default_prompt

    custom_prompt = st.text_area(
        "System Prompt",
        value=saved_prompt,
        height=200,
        label_visibility="collapsed",
        help="This prompt is prepended to every conversation"
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Save Prompt", use_container_width=True, type="primary"):
            DatabaseManager.set_setting("ai_system_prompt", custom_prompt)
            st.success("Prompt saved!")

    with col2:
        if st.button("Reset to Default"):
            DatabaseManager.set_setting("ai_system_prompt", default_prompt)
            st.rerun()

    # Usage info
    with st.expander("Provider Comparison & Pricing"):
        st.markdown("""
        **OpenAI:**
        - gpt-4o-mini: ~$0.001/query (fast, cheap)
        - gpt-4o: ~$0.01/query (capable)
        - o1/o1-mini: ~$0.02-0.15/query (reasoning, slow but thorough)

        **DeepSeek:**
        - deepseek-chat: ~$0.0005/query (very cheap)
        - deepseek-reasoner: ~$0.002/query (best value for complex analysis)

        **Anthropic (Claude):**
        - claude-3-5-haiku: ~$0.001/query (fast)
        - claude-3-5-sonnet: ~$0.003/query (balanced)
        - claude-3-opus: ~$0.015/query (most capable)

        **Groq (Free tier available!):**
        - llama-3.3-70b: Free tier, very fast
        - mixtral-8x7b: Free tier, good reasoning

        **Recommendation for Options Analysis:**
        For complex Greeks calculations and strategy evaluation, try:
        1. DeepSeek Reasoner (best value)
        2. OpenAI o1-mini (if you have OpenAI credits)
        3. Claude 3.5 Sonnet (great general capability)
        """)


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

    # Sync Portfolio section - only show when connected
    if connected:
        st.markdown("---")
        st.markdown("#### Sync Portfolio from IBKR")
        st.caption("Import your stocks and options positions from IBKR")

        # Account selector
        client = get_ibkr_client()
        accounts = client.get_managed_accounts()

        if accounts:
            # Get saved account preference
            saved_account = DatabaseManager.get_setting("ibkr_sync_account")
            default_index = 0
            if saved_account and saved_account in accounts:
                default_index = accounts.index(saved_account)

            selected_account = st.selectbox(
                "Select Account",
                accounts,
                index=default_index,
                help="Choose which IBKR account to sync positions from"
            )

            # Save selection
            if selected_account != saved_account:
                DatabaseManager.set_setting("ibkr_sync_account", selected_account)
        else:
            selected_account = None
            st.warning("No accounts found. Try reconnecting to IBKR.")

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Sync All", use_container_width=True, type="primary", disabled=not selected_account):
                with st.spinner(f"Syncing portfolio from {selected_account}..."):
                    try:
                        positions = client.get_positions(account=selected_account)

                        if positions:
                            from database.models import Position, StockHolding
                            from datetime import date as date_type

                            stocks_synced = 0
                            options_synced = 0

                            for pos in positions:
                                try:
                                    sec_type = pos.get('sec_type', '')
                                    symbol = pos.get('symbol', '')
                                    quantity = pos.get('quantity', 0)
                                    avg_cost = pos.get('avg_cost', 0)
                                    con_id = pos.get('con_id')

                                    # Stock position
                                    if sec_type == 'STK':
                                        holding = StockHolding(
                                            symbol=symbol,
                                            quantity=int(quantity),
                                            avg_cost=avg_cost,
                                            market_value=abs(quantity * avg_cost) if avg_cost else None,
                                            ibkr_con_id=con_id
                                        )
                                        DatabaseManager.upsert_stock_holding(holding)
                                        stocks_synced += 1

                                    # Options position
                                    elif sec_type == 'OPT':
                                        right = pos.get('right', '')
                                        option_type = "CALL" if right == "C" else "PUT"

                                        # Parse expiry date
                                        expiry_str = pos.get('expiry', '')
                                        expiry = None
                                        if expiry_str and len(expiry_str) == 8:
                                            expiry = date_type(
                                                int(expiry_str[:4]),
                                                int(expiry_str[4:6]),
                                                int(expiry_str[6:8])
                                            )

                                        # Check if position already exists
                                        existing = DatabaseManager.get_open_positions()
                                        exists = any(
                                            p.ibkr_con_id == con_id
                                            for p in existing
                                            if p.ibkr_con_id
                                        )

                                        if not exists:
                                            new_pos = Position(
                                                underlying=symbol,
                                                option_type=option_type,
                                                strike=pos.get('strike', 0),
                                                expiry=expiry,
                                                quantity=abs(int(quantity)),
                                                premium_collected=abs(avg_cost) / 100 if avg_cost else 0,
                                                open_date=date_type.today(),
                                                status="OPEN",
                                                strategy_type="CSP" if option_type == "PUT" else "CC",
                                                ibkr_con_id=con_id
                                            )
                                            DatabaseManager.add_position(new_pos)
                                            options_synced += 1

                                except Exception as e:
                                    st.warning(f"Skipped {pos.get('symbol', 'unknown')}: {e}")
                                    continue

                            msg_parts = []
                            if stocks_synced > 0:
                                msg_parts.append(f"{stocks_synced} stock(s)")
                            if options_synced > 0:
                                msg_parts.append(f"{options_synced} option(s)")

                            if msg_parts:
                                st.success(f"Synced {' and '.join(msg_parts)} from IBKR!")
                            else:
                                st.info("No new positions to sync (all positions already exist)")
                        else:
                            st.info("No positions found in IBKR")

                    except Exception as e:
                        st.error(f"Error syncing: {str(e)}")

        with col2:
            if st.button("Clear Stocks", use_container_width=True):
                DatabaseManager.clear_all_stock_holdings()
                st.success("Stock holdings cleared")
                st.rerun()

        with col3:
            st.caption("Syncs both stocks and options. Stocks are replaced on each sync. Options are added if new (matched by contract ID).")

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


def render_profile_settings():
    """Render profile export/import settings."""
    import json
    from datetime import datetime as dt

    st.markdown("#### Profile Backup & Restore")
    st.caption("Export your settings to a file or import from a previous backup.")

    # Current profile info
    all_settings = DatabaseManager.get_all_settings()
    watchlists = DatabaseManager.get_all_watchlists()

    # Count of saved items
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Settings", len(all_settings))
    with col2:
        st.metric("Watchlists", len(watchlists))
    with col3:
        total_symbols = sum(len(wl.symbols) for wl in watchlists)
        st.metric("Symbols", total_symbols)

    st.markdown("---")

    # Export section
    st.markdown("#### Export Profile")
    st.caption("Download all your settings, watchlists, and scanner presets.")

    # Build export data
    export_data = {
        "version": "1.0",
        "exported_at": dt.now().isoformat(),
        "settings": {},
        "watchlists": []
    }

    # Add settings (mask API keys in display but include in export)
    for key, value in all_settings.items():
        export_data["settings"][key] = value

    # Add watchlists
    for wl in watchlists:
        export_data["watchlists"].append({
            "name": wl.name,
            "description": wl.description,
            "symbols": wl.symbols
        })

    # Create download button
    export_json = json.dumps(export_data, indent=2)
    filename = f"options_buddy_profile_{dt.now().strftime('%Y%m%d_%H%M%S')}.json"

    col1, col2 = st.columns([2, 1])
    with col1:
        st.download_button(
            label="Download Profile Backup",
            data=export_json,
            file_name=filename,
            mime="application/json",
            use_container_width=True,
            type="primary"
        )
    with col2:
        # Show what's included
        with st.expander("What's included?"):
            st.markdown("""
            - AI provider & model settings
            - API keys (encrypted in file)
            - System prompt customization
            - Scanner presets
            - Alert thresholds
            - Watchlists & symbols
            """)

    st.markdown("---")

    # Import section
    st.markdown("#### Import Profile")
    st.caption("Restore settings from a backup file.")

    uploaded_file = st.file_uploader(
        "Choose a profile backup file",
        type=["json"],
        label_visibility="collapsed"
    )

    if uploaded_file is not None:
        try:
            import_data = json.loads(uploaded_file.read().decode('utf-8'))

            # Show preview
            st.markdown("**Preview:**")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Settings", len(import_data.get("settings", {})))
            with col2:
                st.metric("Watchlists", len(import_data.get("watchlists", [])))
            with col3:
                exported_at = import_data.get("exported_at", "Unknown")
                if exported_at != "Unknown":
                    try:
                        exp_date = dt.fromisoformat(exported_at)
                        exported_at = exp_date.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                st.caption(f"Exported: {exported_at}")

            # Show settings that will be imported
            with st.expander("Settings to import"):
                for key in import_data.get("settings", {}).keys():
                    if "api_key" in key:
                        st.markdown(f"- `{key}`: \\*\\*\\*hidden\\*\\*\\*")
                    else:
                        value = import_data["settings"][key]
                        display_value = value[:50] + "..." if len(str(value)) > 50 else value
                        st.markdown(f"- `{key}`: {display_value}")

            # Import options
            st.markdown("**Import Options:**")
            col1, col2 = st.columns(2)
            with col1:
                import_settings = st.checkbox("Import settings", value=True)
                import_watchlists = st.checkbox("Import watchlists", value=True)
            with col2:
                overwrite_existing = st.checkbox("Overwrite existing", value=False,
                                                  help="If unchecked, only add new items")

            if st.button("Import Profile", type="primary", use_container_width=True):
                imported_count = 0

                # Import settings
                if import_settings:
                    for key, value in import_data.get("settings", {}).items():
                        if overwrite_existing or DatabaseManager.get_setting(key) is None:
                            DatabaseManager.set_setting(key, value)
                            imported_count += 1

                # Import watchlists
                if import_watchlists:
                    existing_watchlists = {wl.name for wl in DatabaseManager.get_all_watchlists()}

                    for wl_data in import_data.get("watchlists", []):
                        wl_name = wl_data.get("name", "")
                        if wl_name and (overwrite_existing or wl_name not in existing_watchlists):
                            # Create watchlist if it doesn't exist
                            if wl_name not in existing_watchlists:
                                try:
                                    wl_id = DatabaseManager.create_watchlist(
                                        wl_name,
                                        wl_data.get("description", "")
                                    )
                                except:
                                    # Already exists, find it
                                    wl_id = None
                                    for wl in DatabaseManager.get_all_watchlists():
                                        if wl.name == wl_name:
                                            wl_id = wl.id
                                            break
                            else:
                                # Find existing watchlist
                                wl_id = None
                                for wl in DatabaseManager.get_all_watchlists():
                                    if wl.name == wl_name:
                                        wl_id = wl.id
                                        break

                            # Add symbols
                            if wl_id:
                                for symbol in wl_data.get("symbols", []):
                                    DatabaseManager.add_symbol_to_watchlist(wl_id, symbol)
                                imported_count += 1

                st.success(f"Imported {imported_count} items successfully!")
                st.rerun()

        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please select a valid profile backup.")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

    st.markdown("---")

    # Database info
    with st.expander("Database Info"):
        from pathlib import Path
        db_path = Path(__file__).parent.parent / "data_store" / "options_buddy.db"

        if db_path.exists():
            size_kb = db_path.stat().st_size / 1024
            modified = dt.fromtimestamp(db_path.stat().st_mtime)

            st.markdown(f"""
            **Database Location:**
            `{db_path}`

            **Size:** {size_kb:.1f} KB
            **Last Modified:** {modified.strftime('%Y-%m-%d %H:%M:%S')}

            **Tip:** Your settings are stored in this SQLite database file.
            Back it up regularly or use the Export feature above.
            """)
        else:
            st.warning("Database file not found.")


# Run the page
render_settings()
