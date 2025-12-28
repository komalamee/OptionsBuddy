"""
Options Buddy - Main Streamlit Application

A personal options trading platform that leverages Black-Scholes
to identify mispriced options for premium selling strategies.
"""

import streamlit as st
from pathlib import Path
from datetime import datetime, time
import pytz

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


def is_market_open() -> tuple[bool, str]:
    """
    Check if US stock market is currently open.
    Returns (is_open, status_message).
    """
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)

    # Market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
    market_open = time(9, 30)
    market_close = time(16, 0)

    # Check if weekend
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False, "Market Closed (Weekend)"

    current_time = now.time()

    if current_time < market_open:
        return False, "Market Closed (Pre-market)"
    elif current_time > market_close:
        return False, "Market Closed (After-hours)"
    else:
        return True, "Market Open"


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

    # Market status indicator
    market_open, market_status = is_market_open()
    if market_open:
        st.sidebar.success(f"🟢 {market_status}")
    else:
        st.sidebar.warning(f"🟡 {market_status}")
        st.sidebar.caption("Data may be stale or frozen")

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
