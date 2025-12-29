"""
Trade Ideas - AI-generated trade suggestions with ticker cards.
Professional trading UI with intelligent opportunity discovery.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
import random

from database import DatabaseManager, init_database
from components.theme import apply_theme, page_header, ticker_card


# Sample trade ideas - in production, these would come from real analysis
SAMPLE_TRADE_IDEAS = [
    {
        "symbol": "TSLA",
        "name": "Tesla Inc",
        "sentiment": "Bullish",
        "price": "$248.50",
        "change": "+2.4%",
        "iv_rank": "72%",
        "score": 85,
        "strategy": "Iron Condor",
        "rationale": "High IV rank makes premium selling attractive. Range-bound technicals suggest iron condor strategy."
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corp",
        "sentiment": "Bullish",
        "price": "$495.20",
        "change": "+1.8%",
        "iv_rank": "65%",
        "score": 82,
        "strategy": "Cash Secured Put",
        "rationale": "Strong momentum with elevated IV. CSP at support level offers good risk/reward."
    },
    {
        "symbol": "AAPL",
        "name": "Apple Inc",
        "sentiment": "Neutral",
        "price": "$189.75",
        "change": "-0.3%",
        "iv_rank": "45%",
        "score": 68,
        "strategy": "Covered Call",
        "rationale": "Consolidating near highs. If you own shares, covered calls can generate income."
    },
    {
        "symbol": "AMD",
        "name": "AMD Inc",
        "sentiment": "Bullish",
        "price": "$142.30",
        "change": "+3.1%",
        "iv_rank": "58%",
        "score": 75,
        "strategy": "Bull Put Spread",
        "rationale": "Technical breakout with rising momentum. Bull put spread limits risk while capturing upside."
    },
    {
        "symbol": "SPY",
        "name": "S&P 500 ETF",
        "sentiment": "Neutral",
        "price": "$478.50",
        "change": "+0.2%",
        "iv_rank": "32%",
        "score": 55,
        "strategy": "Iron Condor",
        "rationale": "Low volatility environment. Wide iron condor for steady income in range-bound market."
    },
    {
        "symbol": "META",
        "name": "Meta Platforms",
        "sentiment": "Bullish",
        "price": "$358.90",
        "change": "+1.5%",
        "iv_rank": "48%",
        "score": 70,
        "strategy": "Cash Secured Put",
        "rationale": "Strong fundamentals with recent pullback. CSP at support could yield quality entry."
    }
]


def render_ideas_header():
    """Render the trade ideas header with filters."""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search = st.text_input(
            "Search",
            placeholder="Search by symbol or strategy...",
            label_visibility="collapsed"
        )

    with col2:
        strategy_filter = st.selectbox(
            "Strategy",
            ["All Strategies", "Cash Secured Put", "Covered Call", "Iron Condor", "Bull Put Spread", "Bear Call Spread"],
            label_visibility="collapsed"
        )

    with col3:
        sentiment_filter = st.selectbox(
            "Sentiment",
            ["All", "Bullish", "Bearish", "Neutral"],
            label_visibility="collapsed"
        )

    return search, strategy_filter, sentiment_filter


def render_idea_cards(ideas: list):
    """Render trade idea cards in a grid."""
    if not ideas:
        st.markdown('''
        <div style="text-align: center; padding: 60px 20px; color: var(--text-muted);">
            <p style="font-size: 3rem; margin-bottom: 12px;">🔍</p>
            <p style="font-size: 1.1rem; margin-bottom: 8px;">No trade ideas found</p>
            <p style="font-size: 0.9rem;">Try adjusting your filters</p>
        </div>
        ''', unsafe_allow_html=True)
        return

    # Display in 2-column grid
    cols = st.columns(2)

    for i, idea in enumerate(ideas):
        with cols[i % 2]:
            sentiment_class = {
                "Bullish": "bullish",
                "Bearish": "bearish",
                "Neutral": "neutral"
            }.get(idea['sentiment'], "neutral")

            change_class = "text-profit" if idea['change'].startswith("+") else "text-loss"
            score_color = "var(--profit)" if idea['score'] >= 70 else "var(--warning)" if idea['score'] >= 50 else "var(--loss)"

            st.markdown(f'''
            <div class="ob-ticker-card">
                <div class="ob-ticker-header">
                    <div>
                        <div class="ob-ticker-symbol">{idea['symbol']}</div>
                        <div class="ob-ticker-name">{idea['name']}</div>
                    </div>
                    <span class="ob-ticker-badge {sentiment_class}">{idea['sentiment']}</span>
                </div>

                <div class="ob-ticker-stats">
                    <div class="ob-ticker-stat">
                        <div class="ob-ticker-stat-value">{idea['price']}</div>
                        <div class="ob-ticker-stat-label">Price</div>
                    </div>
                    <div class="ob-ticker-stat">
                        <div class="ob-ticker-stat-value {change_class}">{idea['change']}</div>
                        <div class="ob-ticker-stat-label">Change</div>
                    </div>
                    <div class="ob-ticker-stat">
                        <div class="ob-ticker-stat-value">{idea['iv_rank']}</div>
                        <div class="ob-ticker-stat-label">IV Rank</div>
                    </div>
                </div>

                <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span class="ob-tag">{idea['strategy']}</span>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 0.75rem; color: var(--text-muted);">Score</span>
                            <span style="font-weight: 700; color: {score_color};">{idea['score']}</span>
                        </div>
                    </div>
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin: 0; line-height: 1.4;">
                        {idea['rationale']}
                    </p>
                </div>
            </div>
            ''', unsafe_allow_html=True)

            # Action button
            if st.button(f"Analyze {idea['symbol']}", key=f"analyze_{idea['symbol']}", use_container_width=True):
                st.session_state['analyze_symbol'] = idea['symbol']
                st.switch_page("pages/2_advisor.py")

            st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)


def render_portfolio_opportunities():
    """Render opportunities based on user's portfolio."""
    st.markdown('''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">Portfolio-Based Opportunities</h3>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Check for covered call opportunities
    cc_eligible = DatabaseManager.get_covered_call_eligible()

    if cc_eligible:
        st.markdown("##### Covered Call Candidates")

        for stock in cc_eligible[:4]:
            st.markdown(f'''
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: var(--card); border-radius: 10px; margin-bottom: 8px;">
                <div>
                    <span style="font-weight: 600; font-size: 1.1rem;">{stock['symbol']}</span>
                    <span style="color: var(--text-muted); margin-left: 12px;">{stock['quantity']} shares ({stock['cc_lots']} lots)</span>
                </div>
                <span class="ob-badge ob-badge-profit">CC Ready</span>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div style="text-align: center; padding: 30px; color: var(--text-muted);">
            <p>No stock holdings with 100+ shares for covered calls</p>
            <p style="font-size: 0.85rem;">Sync your portfolio from IBKR in Settings</p>
        </div>
        ''', unsafe_allow_html=True)

    # Check for expiring positions that could be rolled
    positions = DatabaseManager.get_open_positions()
    expiring = [p for p in positions if p.days_to_expiry <= 14]

    if expiring:
        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)
        st.markdown("##### Roll Candidates")

        for pos in expiring[:4]:
            dte = pos.days_to_expiry
            urgency_class = "ob-badge-loss" if dte <= 3 else "ob-badge-warning" if dte <= 7 else "ob-badge-info"

            st.markdown(f'''
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: var(--card); border-radius: 10px; margin-bottom: 8px;">
                <div>
                    <span style="font-weight: 600;">{pos.underlying}</span>
                    <span style="color: var(--text-muted); margin-left: 8px;">${pos.strike:.0f} {pos.option_type}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span class="{urgency_class}">{dte}d left</span>
                    <span class="ob-tag">Consider Roll</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)


def render_market_overview():
    """Render a simple market overview section."""
    st.markdown('''
    <div class="ob-card">
        <div class="ob-card-header">
            <h3 class="ob-card-title">Market Conditions</h3>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # This would connect to real market data in production
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('''
        <div style="text-align: center; padding: 16px; background: var(--card); border-radius: 10px;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">VIX</div>
            <div style="font-size: 1.5rem; font-weight: 700;">14.2</div>
            <div style="font-size: 0.8rem; color: var(--profit);">Low Volatility</div>
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        st.markdown('''
        <div style="text-align: center; padding: 16px; background: var(--card); border-radius: 10px;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Market Trend</div>
            <div style="font-size: 1.5rem; font-weight: 700;">↗</div>
            <div style="font-size: 0.8rem; color: var(--profit);">Bullish</div>
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        st.markdown('''
        <div style="text-align: center; padding: 16px; background: var(--card); border-radius: 10px;">
            <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Premium Env.</div>
            <div style="font-size: 1.5rem; font-weight: 700;">Med</div>
            <div style="font-size: 0.8rem; color: var(--warning);">Moderate</div>
        </div>
        ''', unsafe_allow_html=True)


def render_ideas_page():
    """Render the trade ideas page."""
    # Apply theme
    apply_theme()

    # Initialize database
    init_database()

    # Page header
    st.markdown(page_header("Trade Ideas", "AI-powered trade suggestions based on market conditions"), unsafe_allow_html=True)

    # Market overview
    render_market_overview()

    st.markdown("<div style='height: 24px'></div>", unsafe_allow_html=True)

    # Main content
    col_ideas, col_portfolio = st.columns([2, 1])

    with col_ideas:
        st.markdown('''
        <div class="ob-card">
            <div class="ob-card-header">
                <h3 class="ob-card-title">AI Trade Suggestions</h3>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Filters
        search, strategy_filter, sentiment_filter = render_ideas_header()

        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

        # Filter ideas
        filtered_ideas = SAMPLE_TRADE_IDEAS.copy()

        if search:
            search_lower = search.lower()
            filtered_ideas = [
                i for i in filtered_ideas
                if search_lower in i['symbol'].lower() or search_lower in i['strategy'].lower()
            ]

        if strategy_filter != "All Strategies":
            filtered_ideas = [i for i in filtered_ideas if i['strategy'] == strategy_filter]

        if sentiment_filter != "All":
            filtered_ideas = [i for i in filtered_ideas if i['sentiment'] == sentiment_filter]

        # Sort by score
        filtered_ideas = sorted(filtered_ideas, key=lambda x: x['score'], reverse=True)

        # Render cards
        render_idea_cards(filtered_ideas)

    with col_portfolio:
        # Portfolio opportunities
        render_portfolio_opportunities()

        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

        # Refresh button
        if st.button("Refresh Ideas", type="primary", use_container_width=True):
            st.rerun()

        st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

        # Info box
        st.markdown('''
        <div style="background: var(--info-bg); border-radius: 10px; padding: 16px;">
            <p style="font-weight: 600; margin: 0 0 8px 0; color: var(--info);">About Trade Ideas</p>
            <p style="font-size: 0.85rem; color: var(--text-muted); margin: 0; line-height: 1.5;">
                These suggestions are generated based on technical analysis, IV rank, and market conditions.
                Always do your own research before trading.
            </p>
        </div>
        ''', unsafe_allow_html=True)


# Run the page
render_ideas_page()
