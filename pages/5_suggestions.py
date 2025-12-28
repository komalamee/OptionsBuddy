"""
Suggestions Page - Position-based recommendations.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime

from database import DatabaseManager, init_database
from components.styles import apply_global_styles, COLORS


def render_suggestions():
    """Render the suggestions page."""
    # Apply global styles
    apply_global_styles()

    # Compact header
    st.markdown("""
    <div style="margin-bottom: 0.75rem;">
        <h1 style="margin: 0; font-size: 1.75rem;">Suggestions</h1>
        <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9rem;">Smart recommendations based on your positions</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize database
    init_database()

    # Get open positions
    positions = DatabaseManager.get_open_positions()

    if not positions:
        st.markdown("""
        <div class="ob-empty-state">
            <p style="margin: 0;">No open positions. Add positions to get personalized suggestions.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Categorize positions by urgency
    expiring_critical = [p for p in positions if p.days_to_expiry <= 3]
    expiring_soon = [p for p in positions if 3 < p.days_to_expiry <= 7]
    approaching = [p for p in positions if 7 < p.days_to_expiry <= 14]
    stable = [p for p in positions if p.days_to_expiry > 14]

    # Summary metrics - compact row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if expiring_critical:
            st.metric("Critical", len(expiring_critical), delta="action needed",
                      delta_color="inverse", help="Expiring in 3 days or less")
        else:
            st.metric("Critical", 0, help="Expiring in 3 days or less")

    with col2:
        st.metric("Expiring Soon", len(expiring_soon), help="Expiring in 4-7 days")

    with col3:
        st.metric("Approaching", len(approaching), help="Expiring in 8-14 days")

    with col4:
        st.metric("Stable", len(stable), help="More than 14 days to expiry")

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # Critical alerts - prominent
    if expiring_critical:
        st.markdown("""
        <div class="ob-banner-error">
            <strong style="font-size: 1.1rem;">Action Required</strong>
            <span class="text-muted" style="margin-left: 12px;">Positions expiring within 3 days</span>
        </div>
        """, unsafe_allow_html=True)

        for pos in expiring_critical:
            _render_position_suggestion(pos, "critical")

    # Expiring soon
    if expiring_soon:
        st.markdown("#### Expiring This Week")

        for pos in expiring_soon:
            _render_position_suggestion(pos, "warning")

    # Roll opportunities
    st.markdown("#### Roll Opportunities")

    connected = st.session_state.get('ibkr_connected', False)

    if not connected:
        st.markdown("""
        <div class="ob-banner-warning">
            <strong>Not Connected</strong>
            <span class="text-muted" style="margin-left: 12px;">Connect to IBKR to see live roll opportunities with pricing.</span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([4, 1, 4])
        with col2:
            if st.button("Settings", key="goto_settings_roll"):
                st.switch_page("pages/6_settings.py")
    else:
        positions_to_roll = [p for p in positions if p.days_to_expiry <= 14]
        if positions_to_roll:
            for pos in positions_to_roll:
                st.markdown(f"""
                <div class="ob-synced-item">
                    <strong>{pos.underlying}</strong> ${pos.strike:.0f} {pos.option_type} - {pos.days_to_expiry}d
                </div>
                """, unsafe_allow_html=True)
            st.caption("Click 'Find Roll Options' on positions to fetch live opportunities.")
        else:
            st.info("No positions within 14 DTE that need rolling.")

    # Post-assignment ideas
    st.markdown("#### Post-Assignment Ideas")

    assigned = [p for p in DatabaseManager.get_all_positions() if p.status == "ASSIGNED"]

    if assigned:
        for pos in assigned:
            st.markdown(f"""
            <div class="ob-stock-ref">
                <strong>{pos.underlying}</strong> assigned at ${pos.strike:.2f}
                <div class="text-muted" style="font-size: 0.85rem; margin-top: 4px;">
                    Consider selling covered calls at ${pos.strike + 5:.0f}+ for income.
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("When puts are assigned, covered call suggestions will appear here.")

    # Profit taking
    st.markdown("#### Profit Taking")

    # Show positions that might be good for early close
    profitable_candidates = [p for p in positions if p.days_to_expiry > 7]
    if profitable_candidates:
        st.caption("Consider closing positions early when 50%+ profit captured to free capital.")
        for pos in profitable_candidates[:3]:  # Show top 3
            st.markdown(f"""
            <div class="ob-position-normal" style="padding: 8px 12px; font-size: 0.85rem;">
                {pos.underlying} ${pos.strike:.0f} {pos.option_type} | {pos.days_to_expiry}d | Premium: ${pos.premium_collected:.2f}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No positions available for profit taking analysis.")

    # Portfolio suggestions
    st.markdown("#### Portfolio Analysis")

    # Diversification check
    symbols = [p.underlying for p in positions]
    unique_symbols = set(symbols)

    col1, col2 = st.columns(2)

    with col1:
        # Concentration
        if len(positions) > 0 and len(unique_symbols) < len(positions) * 0.5:
            st.markdown(f"""
            <div class="ob-position-warning" style="padding: 10px 14px; font-size: 0.85rem;">
                <strong>Concentration Warning</strong><br>
                {len(unique_symbols)} unique symbols in {len(positions)} positions.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success(f"Good diversification: {len(unique_symbols)} symbols")

    with col2:
        # Strategy mix
        strategies = [p.strategy_type for p in positions]
        strategy_counts = {}
        for s in strategies:
            strategy_counts[s] = strategy_counts.get(s, 0) + 1

        st.markdown("**Strategy Distribution**")
        for strategy, count in strategy_counts.items():
            pct = count / len(positions) * 100
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 2px;">
                <span>{strategy}</span>
                <span>{count} ({pct:.0f}%)</span>
            </div>
            """, unsafe_allow_html=True)


def _render_position_suggestion(pos, level: str):
    """Render a position with suggestions."""
    if level == "critical":
        card_class = "ob-position-critical"
        badge_class = "ob-badge-critical"
    else:
        card_class = "ob-position-warning"
        badge_class = "ob-badge-warning"

    st.markdown(f"""
    <div class="{card_class}" style="padding: 14px 18px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 1.1rem; font-weight: 600;">
                {pos.underlying} ${pos.strike:.0f} {pos.option_type}
            </span>
            <span class="{badge_class}">{pos.days_to_expiry}d</span>
        </div>
        <div class="text-muted" style="font-size: 0.85rem;">
            {pos.strategy_type} | Premium: ${pos.premium_collected:.2f} |
            Exp: {pos.expiry.strftime('%m/%d') if pos.expiry else 'N/A'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("Find Rolls", key=f"roll_{pos.id}"):
            if st.session_state.get('ibkr_connected', False):
                st.info("Fetching roll opportunities...")
            else:
                st.warning("Connect to IBKR first")
    with col2:
        if st.button("Close", key=f"close_{pos.id}"):
            st.session_state[f"close_dialog_{pos.id}"] = True

    # Recommendations based on option type
    if pos.option_type == "PUT":
        st.caption("Options: Let expire (if OTM), Roll out, Close position, or Take assignment")
    else:
        st.caption("Options: Let expire (if OTM), Roll out, or Close to keep shares")

    st.markdown("<div style='height: 4px'></div>", unsafe_allow_html=True)


# Run the page
render_suggestions()
