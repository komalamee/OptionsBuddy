"""
Options Buddy - Main Application Entry Point

Redirects to Dashboard as the primary landing experience.
"""

import streamlit as st

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

# Redirect to Dashboard immediately
st.switch_page("pages/1_dashboard.py")
