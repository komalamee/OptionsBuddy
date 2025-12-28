"""
AI Assistant Page - Chat with an LLM that has context about your positions.
"""

import streamlit as st
from datetime import date, datetime

from database import DatabaseManager, init_database
from components.styles import apply_global_styles


def get_portfolio_context() -> str:
    """Build context string about user's current positions and portfolio."""
    positions = DatabaseManager.get_open_positions()
    stats = DatabaseManager.get_position_stats()

    if not positions:
        return "The user currently has no open positions."

    # Build position summary
    lines = ["## Current Portfolio\n"]

    # Summary stats
    total_premium = sum(p.premium_collected * p.quantity * 100 for p in positions)
    lines.append(f"**Open Positions:** {len(positions)}")
    lines.append(f"**Total Premium Collected:** ${total_premium:,.0f}")
    lines.append(f"**Win Rate:** {stats.get('win_rate', 0):.0f}%\n")

    # Position details
    lines.append("### Positions:\n")

    for pos in positions:
        dte = pos.days_to_expiry
        urgency = ""
        if dte <= 3:
            urgency = " [CRITICAL - expiring soon!]"
        elif dte <= 7:
            urgency = " [Expiring this week]"

        lines.append(
            f"- **{pos.underlying}** ${pos.strike:.0f} {pos.option_type} | "
            f"{pos.strategy_type} | {dte}d to expiry | "
            f"Premium: ${pos.premium_collected:.2f}/share | "
            f"Qty: {pos.quantity}{urgency}"
        )

    # Add IBKR connection status
    connected = st.session_state.get('ibkr_connected', False)
    lines.append(f"\n**IBKR Status:** {'Connected' if connected else 'Not connected'}")

    return "\n".join(lines)


def get_live_price(symbol: str) -> str:
    """Fetch live price from IBKR if connected."""
    connected = st.session_state.get('ibkr_connected', False)
    if not connected:
        return f"Cannot fetch price for {symbol} - IBKR not connected."

    try:
        from data.ibkr_client import get_ibkr_client
        client = get_ibkr_client()
        price = client.get_stock_price(symbol)
        if price:
            return f"Current price for {symbol}: ${price:.2f}"
        return f"Could not fetch price for {symbol}"
    except Exception as e:
        return f"Error fetching price: {str(e)}"


def chat_with_openai(messages: list, api_key: str, model: str) -> str:
    """Send messages to OpenAI and get response."""
    import openai

    client = openai.OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=1500
    )

    return response.choices[0].message.content


def render_assistant():
    """Render the AI assistant page."""
    # Apply global styles
    apply_global_styles()

    # Compact header
    st.markdown("""
    <div style="margin-bottom: 0.75rem;">
        <h1 style="margin: 0; font-size: 1.75rem;">AI Assistant</h1>
        <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9rem;">Chat about your positions and options strategies</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize
    init_database()

    # Check for API key
    api_key = DatabaseManager.get_setting("openai_api_key")
    has_key = bool(api_key and len(api_key) > 10)

    if not has_key:
        st.markdown("""
        <div class="ob-banner-warning">
            <strong>API Key Required</strong>
            <span class="text-muted" style="margin-left: 12px;">Add your OpenAI API key in Settings to use the AI Assistant</span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("Go to Settings", use_container_width=True, type="primary"):
                st.switch_page("pages/6_settings.py")

        st.markdown("""
        <div class="ob-empty-state">
            <p style="margin: 0;">Configure your OpenAI API key to start chatting with the AI assistant.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Get model
    model = DatabaseManager.get_setting("openai_model") or "gpt-4o-mini"

    # Get system prompt (user customizable or default)
    default_system_prompt = """You are an expert options trading assistant for Options Buddy. You help analyze positions, suggest strategies, and provide actionable recommendations.

Key behaviors:
- Be concise and direct
- Focus on premium selling strategies (CSP, covered calls, spreads)
- Consider risk management and position sizing
- When discussing specific positions, reference the user's actual data
- Explain your reasoning for recommendations
- Never recommend naked short calls without proper context

You have access to the user's current portfolio data which will be provided with each message."""

    system_prompt = DatabaseManager.get_setting("ai_system_prompt") or default_system_prompt

    # Connection status
    connected = st.session_state.get('ibkr_connected', False)

    col1, col2 = st.columns([3, 1])
    with col1:
        if connected:
            st.markdown('<span class="text-profit" style="font-size: 0.85rem;">IBKR Connected - Live data available</span>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<span class="text-warning" style="font-size: 0.85rem;">IBKR Offline - Using stored positions only</span>',
                        unsafe_allow_html=True)

    with col2:
        st.caption(f"Model: {model}")

    st.markdown("---")

    # Initialize chat history in session state
    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = []

    # Display chat history
    for message in st.session_state.assistant_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your positions, strategies, or options..."):
        # Add user message to history
        st.session_state.assistant_messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build context-aware messages for API
        portfolio_context = get_portfolio_context()

        # Check if user is asking for a live price
        price_info = ""
        if connected and any(word in prompt.lower() for word in ["price", "current", "quote", "trading at"]):
            # Try to extract symbol from prompt
            import re
            symbols = re.findall(r'\b[A-Z]{1,5}\b', prompt.upper())
            for sym in symbols:
                if sym not in ["I", "A", "THE", "FOR", "AT", "IS", "IT", "TO", "OF", "AND", "OR"]:
                    price_result = get_live_price(sym)
                    if "Current price" in price_result:
                        price_info = f"\n\n**Live Data:** {price_result}"
                        break

        # Build full system message with context
        full_system = f"{system_prompt}\n\n---\n\n{portfolio_context}{price_info}"

        messages = [
            {"role": "system", "content": full_system}
        ]

        # Add conversation history (last 10 messages to manage tokens)
        for msg in st.session_state.assistant_messages[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = chat_with_openai(messages, api_key, model)
                    st.markdown(response)

                    # Add assistant response to history
                    st.session_state.assistant_messages.append(
                        {"role": "assistant", "content": response}
                    )
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.assistant_messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

    # Sidebar with quick actions
    with st.sidebar:
        st.markdown("### Quick Questions")

        if st.button("What positions need attention?", use_container_width=True):
            st.session_state.pending_question = "Which of my positions need attention right now? Any expiring soon or at risk?"
            st.rerun()

        if st.button("Roll suggestions", use_container_width=True):
            st.session_state.pending_question = "What roll opportunities do you see for my current positions?"
            st.rerun()

        if st.button("Portfolio analysis", use_container_width=True):
            st.session_state.pending_question = "Analyze my current portfolio. How am I doing? Any concerns?"
            st.rerun()

        if st.button("New trade ideas", use_container_width=True):
            st.session_state.pending_question = "Based on my portfolio, what new trades would you suggest to generate premium?"
            st.rerun()

        st.markdown("---")

        if st.button("Clear Chat", use_container_width=True):
            st.session_state.assistant_messages = []
            st.rerun()

    # Handle pending questions from sidebar
    if "pending_question" in st.session_state:
        question = st.session_state.pending_question
        del st.session_state.pending_question

        # Add to chat
        st.session_state.assistant_messages.append({"role": "user", "content": question})

        # Build context
        portfolio_context = get_portfolio_context()
        full_system = f"{system_prompt}\n\n---\n\n{portfolio_context}"

        messages = [{"role": "system", "content": full_system}]
        for msg in st.session_state.assistant_messages[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            response = chat_with_openai(messages, api_key, model)
            st.session_state.assistant_messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.session_state.assistant_messages.append({"role": "assistant", "content": f"Error: {str(e)}"})

        st.rerun()


# Run the page
render_assistant()
