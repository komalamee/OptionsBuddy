"""
Options Buddy - Main Streamlit Application

A personal options trading platform that leverages Black-Scholes
to identify mispriced options for premium selling strategies.
"""

import streamlit as st
from pathlib import Path

# Configure the app
st.set_page_config(
    page_title="Options Buddy",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first run
from database import init_database
init_database()


def main():
    """Main application entry point."""

    # Sidebar header
    st.sidebar.title("📈 Options Buddy")
    st.sidebar.markdown("---")

    # Navigation
    pages = {
        "🏠 Dashboard": "pages/1_dashboard.py",
        "🔍 Scanner": "pages/2_scanner.py",
        "📊 Analyzer": "pages/3_analyzer.py",
        "💼 Positions": "pages/4_positions.py",
        "💡 Suggestions": "pages/5_suggestions.py",
        "⚙️ Settings": "pages/6_settings.py"
    }

    # Check IBKR connection status
    if 'ibkr_connected' not in st.session_state:
        st.session_state.ibkr_connected = False

    # Connection indicator in sidebar
    if st.session_state.ibkr_connected:
        st.sidebar.success("🟢 IBKR Connected")
    else:
        st.sidebar.warning("🔴 IBKR Disconnected")

    st.sidebar.markdown("---")

    # Page selection
    selection = st.sidebar.radio(
        "Navigate",
        list(pages.keys()),
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0.0 | Read-Only Mode")

    # Load the selected page
    page_path = Path(__file__).parent / pages[selection]

    if page_path.exists():
        # Execute the page
        with open(page_path, 'r') as f:
            exec(f.read(), {'__name__': '__main__'})
    else:
        st.error(f"Page not found: {page_path}")


if __name__ == "__main__":
    main()
