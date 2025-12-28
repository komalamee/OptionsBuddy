"""
Global styles and UI components for Options Buddy.
Provides consistent styling, reduced padding, and trading-specific color schemes.
"""

import streamlit as st


def apply_global_styles():
    """Apply global CSS styles to reduce padding and improve layout."""
    st.markdown("""
    <style>
    /* Reduce main container padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }

    /* Compact metrics */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 12px 16px;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.8;
    }

    /* Softer borders on expanders */
    [data-testid="stExpander"] {
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 8px !important;
    }

    /* Compact dataframes */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 8px !important;
    }

    /* Better button styling */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    /* Compact form inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: 6px !important;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
    }

    /* Sidebar refinements */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0e1117 0%, #1a1a2e 100%);
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
    }

    /* Alert styling - softer */
    .stAlert {
        border-radius: 8px !important;
        border-left-width: 4px !important;
    }

    /* Cards/containers */
    .element-container {
        margin-bottom: 0.5rem !important;
    }

    /* Markdown refinements */
    .stMarkdown h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Horizontal rule */
    hr {
        margin: 1rem 0 !important;
        border-color: rgba(128, 128, 128, 0.2) !important;
    }
    </style>
    """, unsafe_allow_html=True)


def style_profit_loss(value: float) -> str:
    """Return styled HTML for profit/loss values."""
    if value > 0:
        return f'<span style="color: #00d26a; font-weight: 600;">+${value:,.2f}</span>'
    elif value < 0:
        return f'<span style="color: #ff4757; font-weight: 600;">-${abs(value):,.2f}</span>'
    else:
        return f'<span style="color: #888;">$0.00</span>'


def style_dte_badge(dte: int) -> str:
    """Return styled HTML badge for days to expiry."""
    if dte <= 3:
        bg_color = "#ff4757"
        label = "CRITICAL"
    elif dte <= 7:
        bg_color = "#ffa502"
        label = "EXPIRING"
    elif dte <= 14:
        bg_color = "#3742fa"
        label = "WATCH"
    else:
        bg_color = "#2ed573"
        label = "STABLE"

    return f'''
    <span style="
        background: {bg_color};
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    ">{dte}d - {label}</span>
    '''


def position_card(symbol: str, strike: float, option_type: str,
                  dte: int, premium: float, strategy: str,
                  pnl: float = None) -> str:
    """Generate HTML for a compact position card."""
    dte_badge = style_dte_badge(dte)
    pnl_html = style_profit_loss(pnl) if pnl is not None else ""

    return f'''
    <div style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 1.2rem; font-weight: 700;">{symbol}</span>
            {dte_badge}
        </div>
        <div style="display: flex; gap: 16px; font-size: 0.9rem; opacity: 0.9;">
            <span>${strike:.0f} {option_type}</span>
            <span>|</span>
            <span>{strategy}</span>
            <span>|</span>
            <span>Premium: ${premium:.2f}</span>
        </div>
        {f'<div style="margin-top: 8px; font-size: 1rem;">P/L: {pnl_html}</div>' if pnl is not None else ''}
    </div>
    '''


def metric_card(label: str, value: str, delta: str = None,
                delta_color: str = "normal") -> str:
    """Generate HTML for a compact metric card."""
    delta_html = ""
    if delta:
        color = "#00d26a" if delta_color == "normal" else "#ff4757"
        delta_html = f'<div style="color: {color}; font-size: 0.85rem;">{delta}</div>'

    return f'''
    <div style="
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    ">
        <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.7; margin-bottom: 4px;">
            {label}
        </div>
        <div style="font-size: 1.5rem; font-weight: 700;">
            {value}
        </div>
        {delta_html}
    </div>
    '''


def alert_banner(message: str, level: str = "info") -> str:
    """Generate HTML for an alert banner."""
    colors = {
        "critical": ("#ff4757", "#2d1f2f"),
        "warning": ("#ffa502", "#2d2a1f"),
        "info": ("#3742fa", "#1f2d3d"),
        "success": ("#2ed573", "#1f2d2a")
    }

    border_color, bg_color = colors.get(level, colors["info"])

    return f'''
    <div style="
        background: {bg_color};
        border-left: 4px solid {border_color};
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin-bottom: 12px;
    ">
        {message}
    </div>
    '''


def section_header(title: str, subtitle: str = None) -> None:
    """Display a styled section header."""
    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <h2 style="margin: 0; font-size: 1.5rem; font-weight: 600;">{title}</h2>
        {f'<p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def quick_action_button(label: str, icon: str = None) -> str:
    """Generate HTML for a quick action button (for use in markdown)."""
    icon_html = f"{icon} " if icon else ""
    return f'''
    <button style="
        background: linear-gradient(135deg, #3742fa 0%, #5352ed 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    ">
        {icon_html}{label}
    </button>
    '''


# Color constants for trading UI
COLORS = {
    "profit": "#00d26a",
    "loss": "#ff4757",
    "neutral": "#888888",
    "critical": "#ff4757",
    "warning": "#ffa502",
    "info": "#3742fa",
    "success": "#2ed573",
    "background_dark": "#0e1117",
    "background_card": "#1a1a2e",
    "border_light": "rgba(255, 255, 255, 0.1)",
    "border_medium": "rgba(128, 128, 128, 0.2)",
}
