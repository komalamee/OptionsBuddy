"""
Design System for Options Buddy - Professional Trading UI
Inspired by modern fintech dashboards with dark/light mode support.
"""

import streamlit as st

# Color Palette
COLORS = {
    # Brand Colors
    "primary": "#3B82F6",        # Blue
    "primary_hover": "#2563EB",
    "secondary": "#6366F1",      # Indigo

    # Status Colors
    "profit": "#10B981",         # Green
    "profit_bg": "rgba(16, 185, 129, 0.1)",
    "loss": "#EF4444",           # Red
    "loss_bg": "rgba(239, 68, 68, 0.1)",
    "warning": "#F59E0B",        # Amber
    "warning_bg": "rgba(245, 158, 11, 0.1)",
    "info": "#3B82F6",           # Blue
    "info_bg": "rgba(59, 130, 246, 0.1)",

    # Dark Theme
    "dark_bg": "#0F172A",        # Slate 900
    "dark_surface": "#1E293B",   # Slate 800
    "dark_card": "#334155",      # Slate 700
    "dark_border": "#475569",    # Slate 600
    "dark_text": "#F8FAFC",      # Slate 50
    "dark_text_muted": "#94A3B8", # Slate 400

    # Light Theme
    "light_bg": "#F8FAFC",       # Slate 50
    "light_surface": "#FFFFFF",
    "light_card": "#F1F5F9",     # Slate 100
    "light_border": "#E2E8F0",   # Slate 200
    "light_text": "#0F172A",     # Slate 900
    "light_text_muted": "#64748B", # Slate 500
}

def get_theme_css():
    """Return comprehensive CSS for the new design system."""
    return """
    <style>
    /* ===== CSS VARIABLES ===== */
    :root {
        --primary: #3B82F6;
        --primary-hover: #2563EB;
        --secondary: #6366F1;
        --profit: #10B981;
        --profit-bg: rgba(16, 185, 129, 0.1);
        --loss: #EF4444;
        --loss-bg: rgba(239, 68, 68, 0.1);
        --warning: #F59E0B;
        --warning-bg: rgba(245, 158, 11, 0.1);
        --info: #3B82F6;
        --info-bg: rgba(59, 130, 246, 0.1);
    }

    /* Dark theme (default in Streamlit dark mode) */
    [data-theme="dark"], .stApp[data-theme="dark"] {
        --bg: #0F172A;
        --surface: #1E293B;
        --card: #334155;
        --border: #475569;
        --text: #F8FAFC;
        --text-muted: #94A3B8;
    }

    /* Light theme */
    [data-theme="light"], .stApp:not([data-theme="dark"]) {
        --bg: #F8FAFC;
        --surface: #FFFFFF;
        --card: #F1F5F9;
        --border: #E2E8F0;
        --text: #0F172A;
        --text-muted: #64748B;
    }

    /* ===== BASE STYLES ===== */
    .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 100% !important;
    }

    /* Hide default Streamlit elements for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ===== TOP NAVIGATION BAR ===== */
    .ob-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        margin-bottom: 24px;
        border-bottom: 1px solid var(--border, rgba(255,255,255,0.1));
    }

    .ob-logo {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .ob-logo-icon {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #3B82F6, #6366F1);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }

    .ob-logo-text {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .ob-nav-tabs {
        display: flex;
        gap: 8px;
    }

    .ob-nav-tab {
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-muted, #94A3B8);
        background: transparent;
        border: none;
        cursor: pointer;
        transition: all 0.2s;
    }

    .ob-nav-tab:hover {
        background: var(--card, rgba(255,255,255,0.05));
        color: var(--text, #F8FAFC);
    }

    .ob-nav-tab.active {
        background: var(--primary);
        color: white;
    }

    .ob-status-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }

    .ob-status-connected {
        background: var(--profit-bg);
        color: var(--profit);
    }

    .ob-status-disconnected {
        background: var(--loss-bg);
        color: var(--loss);
    }

    /* ===== PAGE HEADER ===== */
    .ob-page-header {
        margin-bottom: 24px;
    }

    .ob-page-title {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0 0 4px 0;
        letter-spacing: -0.5px;
    }

    .ob-page-subtitle {
        font-size: 0.9rem;
        color: var(--text-muted, #94A3B8);
        margin: 0;
    }

    /* ===== METRIC CARDS ===== */
    .ob-metrics-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .ob-metric {
        background: var(--surface, #1E293B);
        border: 1px solid var(--border, #475569);
        border-radius: 12px;
        padding: 20px;
    }

    .ob-metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted, #94A3B8);
        margin-bottom: 8px;
    }

    .ob-metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.2;
    }

    .ob-metric-value.profit { color: var(--profit); }
    .ob-metric-value.loss { color: var(--loss); }

    .ob-metric-delta {
        font-size: 0.8rem;
        margin-top: 4px;
    }

    .ob-metric-delta.positive { color: var(--profit); }
    .ob-metric-delta.negative { color: var(--loss); }

    /* Large hero metric */
    .ob-metric-hero {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        border: 1px solid var(--border, #475569);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
    }

    .ob-metric-hero .ob-metric-value {
        font-size: 2.5rem;
    }

    /* ===== CARDS & CONTAINERS ===== */
    .ob-card {
        background: var(--surface, #1E293B);
        border: 1px solid var(--border, #475569);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .ob-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border, rgba(255,255,255,0.1));
    }

    .ob-card-title {
        font-size: 1rem;
        font-weight: 600;
        margin: 0;
    }

    .ob-card-action {
        font-size: 0.8rem;
        color: var(--primary);
        cursor: pointer;
    }

    /* ===== AI ASSISTANT PANEL ===== */
    .ob-ai-panel {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #3B82F6;
        border-radius: 16px;
        padding: 24px;
        position: relative;
        overflow: hidden;
    }

    .ob-ai-panel::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3B82F6, #6366F1, #8B5CF6);
    }

    .ob-ai-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
    }

    .ob-ai-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #3B82F6, #6366F1);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }

    .ob-ai-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
    }

    .ob-ai-subtitle {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin: 0;
    }

    .ob-ai-chat-area {
        background: rgba(0,0,0,0.2);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        min-height: 200px;
        max-height: 400px;
        overflow-y: auto;
    }

    .ob-ai-message {
        margin-bottom: 12px;
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .ob-ai-message.user {
        background: var(--primary);
        color: white;
        margin-left: 20%;
        border-bottom-right-radius: 4px;
    }

    .ob-ai-message.assistant {
        background: var(--card, #334155);
        margin-right: 20%;
        border-bottom-left-radius: 4px;
    }

    .ob-ai-input-area {
        display: flex;
        gap: 12px;
    }

    .ob-ai-suggestions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
    }

    .ob-ai-suggestion {
        padding: 8px 14px;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 20px;
        font-size: 0.8rem;
        color: var(--primary);
        cursor: pointer;
        transition: all 0.2s;
    }

    .ob-ai-suggestion:hover {
        background: rgba(59, 130, 246, 0.2);
        border-color: var(--primary);
    }

    /* ===== DATA TABLES ===== */
    .ob-table-container {
        background: var(--surface, #1E293B);
        border: 1px solid var(--border, #475569);
        border-radius: 12px;
        overflow: hidden;
    }

    .ob-table {
        width: 100%;
        border-collapse: collapse;
    }

    .ob-table th {
        background: var(--card, #334155);
        padding: 12px 16px;
        text-align: left;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted);
        font-weight: 600;
    }

    .ob-table td {
        padding: 14px 16px;
        border-bottom: 1px solid var(--border, rgba(255,255,255,0.05));
        font-size: 0.9rem;
    }

    .ob-table tr:hover td {
        background: rgba(255,255,255,0.02);
    }

    /* ===== POSITION ROW ===== */
    .ob-position-row {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr;
        gap: 16px;
        padding: 16px;
        border-bottom: 1px solid var(--border, rgba(255,255,255,0.05));
        align-items: center;
    }

    .ob-position-row:hover {
        background: rgba(255,255,255,0.02);
    }

    .ob-position-symbol {
        font-weight: 600;
        font-size: 1rem;
    }

    .ob-position-details {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    /* ===== TICKER CARDS (Trade Ideas) ===== */
    .ob-ticker-card {
        background: var(--surface, #1E293B);
        border: 1px solid var(--border, #475569);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: all 0.2s;
    }

    .ob-ticker-card:hover {
        border-color: var(--primary);
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }

    .ob-ticker-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 12px;
    }

    .ob-ticker-symbol {
        font-size: 1.25rem;
        font-weight: 700;
    }

    .ob-ticker-name {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    .ob-ticker-badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .ob-ticker-badge.bullish {
        background: var(--profit-bg);
        color: var(--profit);
    }

    .ob-ticker-badge.bearish {
        background: var(--loss-bg);
        color: var(--loss);
    }

    .ob-ticker-badge.neutral {
        background: var(--warning-bg);
        color: var(--warning);
    }

    .ob-ticker-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 12px;
    }

    .ob-ticker-stat {
        text-align: center;
    }

    .ob-ticker-stat-value {
        font-size: 1.1rem;
        font-weight: 600;
    }

    .ob-ticker-stat-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    /* ===== CHARTS ===== */
    .ob-chart-container {
        background: var(--surface, #1E293B);
        border: 1px solid var(--border, #475569);
        border-radius: 12px;
        padding: 20px;
    }

    .ob-chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }

    .ob-chart-title {
        font-size: 1rem;
        font-weight: 600;
    }

    .ob-chart-period-selector {
        display: flex;
        gap: 4px;
        background: var(--card);
        padding: 4px;
        border-radius: 8px;
    }

    .ob-chart-period {
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
        cursor: pointer;
        color: var(--text-muted);
        border: none;
        background: transparent;
    }

    .ob-chart-period.active {
        background: var(--primary);
        color: white;
    }

    /* ===== BADGES & TAGS ===== */
    .ob-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .ob-badge-profit { background: var(--profit-bg); color: var(--profit); }
    .ob-badge-loss { background: var(--loss-bg); color: var(--loss); }
    .ob-badge-warning { background: var(--warning-bg); color: var(--warning); }
    .ob-badge-info { background: var(--info-bg); color: var(--info); }

    .ob-tag {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 8px;
        background: var(--card);
        border-radius: 4px;
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    /* ===== BUTTONS ===== */
    .ob-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        border: none;
    }

    .ob-btn-primary {
        background: var(--primary);
        color: white;
    }

    .ob-btn-primary:hover {
        background: var(--primary-hover);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }

    .ob-btn-secondary {
        background: var(--card);
        color: var(--text);
        border: 1px solid var(--border);
    }

    .ob-btn-secondary:hover {
        background: var(--surface);
        border-color: var(--primary);
    }

    .ob-btn-ghost {
        background: transparent;
        color: var(--text-muted);
    }

    .ob-btn-ghost:hover {
        background: var(--card);
        color: var(--text);
    }

    /* ===== FORM ELEMENTS ===== */
    .ob-input-group {
        margin-bottom: 16px;
    }

    .ob-input-label {
        display: block;
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--text-muted);
        margin-bottom: 6px;
    }

    /* ===== SIDEBAR STYLES ===== */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: var(--surface, #1E293B) !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: var(--text);
    }

    /* ===== STREAMLIT OVERRIDES ===== */
    .stMetric {
        background: var(--surface, #1E293B) !important;
        border: 1px solid var(--border, #475569) !important;
        border-radius: 12px !important;
        padding: 16px 20px !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: var(--text-muted) !important;
    }

    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 8px 20px !important;
        transition: all 0.2s !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--primary) !important;
        border-color: var(--primary) !important;
    }

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        background: var(--card, #334155) !important;
        border-color: var(--border, #475569) !important;
        border-radius: 8px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface) !important;
        border-radius: 10px !important;
        padding: 4px !important;
        gap: 4px !important;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
    }

    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden !important;
    }

    .stAlert {
        border-radius: 10px !important;
    }

    /* ===== UTILITY CLASSES ===== */
    .text-profit { color: var(--profit) !important; }
    .text-loss { color: var(--loss) !important; }
    .text-warning { color: var(--warning) !important; }
    .text-info { color: var(--info) !important; }
    .text-muted { color: var(--text-muted) !important; }

    .font-bold { font-weight: 700 !important; }
    .font-medium { font-weight: 500 !important; }

    .text-sm { font-size: 0.875rem !important; }
    .text-xs { font-size: 0.75rem !important; }
    .text-lg { font-size: 1.125rem !important; }
    .text-xl { font-size: 1.25rem !important; }
    .text-2xl { font-size: 1.5rem !important; }

    .mb-0 { margin-bottom: 0 !important; }
    .mb-1 { margin-bottom: 0.25rem !important; }
    .mb-2 { margin-bottom: 0.5rem !important; }
    .mb-3 { margin-bottom: 0.75rem !important; }
    .mb-4 { margin-bottom: 1rem !important; }

    .mt-0 { margin-top: 0 !important; }
    .mt-2 { margin-top: 0.5rem !important; }
    .mt-4 { margin-top: 1rem !important; }

    .flex { display: flex !important; }
    .items-center { align-items: center !important; }
    .justify-between { justify-content: space-between !important; }
    .gap-2 { gap: 0.5rem !important; }
    .gap-4 { gap: 1rem !important; }

    /* ===== ANIMATIONS ===== */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .animate-pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .animate-spin {
        animation: spin 1s linear infinite;
    }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--surface);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }
    </style>
    """


def apply_theme():
    """Apply the complete theme to the Streamlit app."""
    st.markdown(get_theme_css(), unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: str = None, delta_positive: bool = True, size: str = "normal") -> str:
    """Generate HTML for a styled metric card."""
    size_class = "ob-metric-hero" if size == "hero" else "ob-metric"
    value_class = ""
    if delta:
        value_class = "profit" if delta_positive else "loss"

    delta_html = ""
    if delta:
        delta_class = "positive" if delta_positive else "negative"
        delta_html = f'<div class="ob-metric-delta {delta_class}">{delta}</div>'

    return f'''
    <div class="{size_class}">
        <div class="ob-metric-label">{label}</div>
        <div class="ob-metric-value {value_class}">{value}</div>
        {delta_html}
    </div>
    '''


def card(title: str, content: str, action: str = None) -> str:
    """Generate HTML for a card container."""
    action_html = f'<span class="ob-card-action">{action}</span>' if action else ''
    return f'''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">{title}</h3>
            {action_html}
        </div>
        {content}
    </div>
    '''


def page_header(title: str, subtitle: str = None) -> str:
    """Generate HTML for a page header."""
    subtitle_html = f'<p class="ob-page-subtitle">{subtitle}</p>' if subtitle else ''
    return f'''
    <div class="ob-page-header">
        <h1 class="ob-page-title">{title}</h1>
        {subtitle_html}
    </div>
    '''


def ticker_card(symbol: str, name: str, sentiment: str, price: str, change: str, iv: str, score: int) -> str:
    """Generate HTML for a trade idea ticker card."""
    badge_class = {
        "bullish": "bullish",
        "bearish": "bearish",
        "neutral": "neutral"
    }.get(sentiment.lower(), "neutral")

    change_class = "text-profit" if change.startswith("+") else "text-loss"

    return f'''
    <div class="ob-ticker-card">
        <div class="ob-ticker-header">
            <div>
                <div class="ob-ticker-symbol">{symbol}</div>
                <div class="ob-ticker-name">{name}</div>
            </div>
            <span class="ob-ticker-badge {badge_class}">{sentiment}</span>
        </div>
        <div class="ob-ticker-stats">
            <div class="ob-ticker-stat">
                <div class="ob-ticker-stat-value">{price}</div>
                <div class="ob-ticker-stat-label">Price</div>
            </div>
            <div class="ob-ticker-stat">
                <div class="ob-ticker-stat-value {change_class}">{change}</div>
                <div class="ob-ticker-stat-label">Change</div>
            </div>
            <div class="ob-ticker-stat">
                <div class="ob-ticker-stat-value">{iv}</div>
                <div class="ob-ticker-stat-label">IV Rank</div>
            </div>
        </div>
    </div>
    '''


def status_badge(text: str, status: str = "info") -> str:
    """Generate HTML for a status badge."""
    return f'<span class="ob-badge ob-badge-{status}">{text}</span>'


def ai_message(content: str, is_user: bool = False) -> str:
    """Generate HTML for an AI chat message."""
    role_class = "user" if is_user else "assistant"
    return f'<div class="ob-ai-message {role_class}">{content}</div>'
