"""
Options Buddy - Main Streamlit Application

A personal options trading platform that leverages Black-Scholes
to identify mispriced options for premium selling strategies.
"""

import streamlit as st
from datetime import datetime, time
import pytz

from components.styles import apply_global_styles

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
    """Main application entry point - Home/Landing page."""

    # Apply global styles
    apply_global_styles()

    # Check IBKR connection status
    if 'ibkr_connected' not in st.session_state:
        st.session_state.ibkr_connected = False

    # Sidebar status indicators (shared across all pages)
    market_open, market_status = is_market_open()
    if market_open:
        st.sidebar.success(f"🟢 {market_status}")
    else:
        st.sidebar.warning(f"🟡 {market_status}")

    if st.session_state.ibkr_connected:
        st.sidebar.success("🟢 IBKR Connected")
    else:
        st.sidebar.warning("🔴 IBKR Disconnected")

    st.sidebar.markdown("---")
    st.sidebar.caption("v1.0.0 | Read-Only Mode")

    # Main content - Home/Landing page
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 2.5rem; margin-bottom: 0.5rem;">📈 Options Buddy</h1>
        <p style="font-size: 1.1rem; opacity: 0.8; max-width: 600px; margin: 0 auto;">
            Find mispriced options using Black-Scholes analysis.
            Identify premium selling opportunities with IV vs HV comparison.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # Feature cards - 3 columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="ob-card" style="text-align: center; min-height: 160px;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">Scanner</h3>
            <p class="text-muted" style="font-size: 0.85rem; margin: 0;">
                Scan your watchlists for mispriced options with customizable filters.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Scanner", use_container_width=True, key="nav_scanner"):
            st.switch_page("pages/2_scanner.py")

    with col2:
        st.markdown("""
        <div class="ob-card" style="text-align: center; min-height: 160px;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">Analyzer</h3>
            <p class="text-muted" style="font-size: 0.85rem; margin: 0;">
                Deep dive into any option with Greeks, volatility analysis, and payoff diagrams.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Analyzer", use_container_width=True, key="nav_analyzer"):
            st.switch_page("pages/3_analyzer.py")

    with col3:
        st.markdown("""
        <div class="ob-card" style="text-align: center; min-height: 160px;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">💼</div>
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">Positions</h3>
            <p class="text-muted" style="font-size: 0.85rem; margin: 0;">
                Track your options positions, sync from IBKR, and monitor P/L.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Positions", use_container_width=True, key="nav_positions"):
            st.switch_page("pages/4_positions.py")

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # Second row of features
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="ob-card" style="text-align: center; min-height: 160px;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">💡</div>
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">Suggestions</h3>
            <p class="text-muted" style="font-size: 0.85rem; margin: 0;">
                Get AI-powered suggestions for rolls, closes, and profit-taking.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Suggestions", use_container_width=True, key="nav_suggestions"):
            st.switch_page("pages/5_suggestions.py")

    with col2:
        st.markdown("""
        <div class="ob-card" style="text-align: center; min-height: 160px;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📋</div>
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">Dashboard</h3>
            <p class="text-muted" style="font-size: 0.85rem; margin: 0;">
                Portfolio overview with alerts and expiring positions at a glance.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Dashboard", use_container_width=True, key="nav_dashboard"):
            st.switch_page("pages/1_dashboard.py")

    with col3:
        st.markdown("""
        <div class="ob-card" style="text-align: center; min-height: 160px;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚙️</div>
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.1rem;">Settings</h3>
            <p class="text-muted" style="font-size: 0.85rem; margin: 0;">
                Connect to IBKR, manage watchlists, and configure preferences.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Settings", use_container_width=True, key="nav_settings"):
            st.switch_page("pages/6_settings.py")

    # Quick start section
    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)

    if not st.session_state.ibkr_connected:
        st.markdown("""
        <div class="ob-banner-info">
            <strong>Quick Start:</strong>
            <span class="text-muted" style="margin-left: 8px;">Connect to IBKR in Settings to enable live data and position sync.</span>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
