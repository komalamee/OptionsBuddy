"""
Dashboard Page - Portfolio overview and alerts.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import DatabaseManager, init_database
from config.constants import STATUS_OPEN
from components.styles import apply_global_styles, COLORS


def render_dashboard():
    """Render the dashboard page."""
    # Apply global styles
    apply_global_styles()

    # Compact header
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <h1 style="margin: 0; font-size: 1.75rem;">Dashboard</h1>
        <p style="margin: 4px 0 0 0; opacity: 0.7; font-size: 0.9rem;">Portfolio overview and alerts</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize database
    init_database()

    # Get data
    open_positions = DatabaseManager.get_open_positions()
    stats = DatabaseManager.get_position_stats()
    total_premium = DatabaseManager.calculate_total_premium_collected()
    open_premium = DatabaseManager.calculate_open_premium()
    win_rate = stats.get('win_rate', 0)

    # Expiring positions for alerts
    expiring_critical = [p for p in open_positions if p.days_to_expiry <= 3]
    expiring_soon = [p for p in open_positions if 3 < p.days_to_expiry <= 7]

    # Alert banner if critical positions exist
    if expiring_critical:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%);
            border-radius: 10px;
            padding: 12px 20px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 12px;
        ">
            <span style="font-size: 1.5rem;">🚨</span>
            <div>
                <strong>{len(expiring_critical)} position(s) expiring within 3 days!</strong>
                <span style="opacity: 0.9;"> Action required.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Top metrics - compact 5-column layout
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Open Positions", len(open_positions))
    with col2:
        st.metric("Total Premium", f"${total_premium:,.0f}")
    with col3:
        st.metric("Open Premium", f"${open_premium:,.0f}")
    with col4:
        st.metric("Win Rate", f"{win_rate:.0f}%")
    with col5:
        critical_count = len(expiring_critical) + len(expiring_soon)
        st.metric("Needs Attention", critical_count, delta="urgent" if expiring_critical else None,
                  delta_color="inverse" if expiring_critical else "off")

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    # Main content area - wider positions table, narrower alerts
    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.markdown("#### Open Positions")

        if open_positions:
            # Build DataFrame with styled data
            position_data = []
            for pos in open_positions:
                dte = pos.days_to_expiry

                # DTE status indicator
                if dte <= 3:
                    dte_display = f"🔴 {dte}"
                elif dte <= 7:
                    dte_display = f"🟡 {dte}"
                else:
                    dte_display = f"🟢 {dte}"

                position_data.append({
                    "Symbol": pos.underlying,
                    "Strike": pos.strike,
                    "Type": pos.option_type,
                    "DTE": dte_display,
                    "Premium": pos.premium_collected,
                    "Strategy": pos.strategy_type,
                    "Expiry": pos.expiry.strftime("%m/%d") if pos.expiry else "-"
                })

            df = pd.DataFrame(position_data)

            # Display with column config
            st.dataframe(
                df,
                column_config={
                    "Strike": st.column_config.NumberColumn("Strike", format="$%.0f"),
                    "Premium": st.column_config.NumberColumn("Premium", format="$%.2f"),
                    "DTE": st.column_config.TextColumn("DTE", width="small"),
                    "Symbol": st.column_config.TextColumn("Symbol", width="small"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                },
                hide_index=True,
                use_container_width=True,
                height=min(400, 50 + len(position_data) * 35)
            )
        else:
            st.info("No open positions. Go to Scanner to find opportunities!")

    with col_side:
        # Alerts section
        st.markdown("#### Alerts")

        if expiring_critical or expiring_soon:
            for pos in expiring_critical:
                st.markdown(f"""
                <div style="
                    background: rgba(255, 71, 87, 0.15);
                    border-left: 3px solid #ff4757;
                    border-radius: 0 6px 6px 0;
                    padding: 8px 12px;
                    margin-bottom: 8px;
                    font-size: 0.85rem;
                ">
                    <strong>{pos.underlying}</strong> ${pos.strike:.0f} {pos.option_type}<br>
                    <span style="color: #ff4757;">Expires in {pos.days_to_expiry}d</span>
                </div>
                """, unsafe_allow_html=True)

            for pos in expiring_soon:
                st.markdown(f"""
                <div style="
                    background: rgba(255, 165, 2, 0.15);
                    border-left: 3px solid #ffa502;
                    border-radius: 0 6px 6px 0;
                    padding: 8px 12px;
                    margin-bottom: 8px;
                    font-size: 0.85rem;
                ">
                    <strong>{pos.underlying}</strong> ${pos.strike:.0f} {pos.option_type}<br>
                    <span style="color: #ffa502;">Expires in {pos.days_to_expiry}d</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No alerts")

        st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

        # Strategy breakdown - compact
        st.markdown("#### By Strategy")
        by_strategy = stats.get('by_strategy', {})
        if by_strategy:
            for strategy, count in by_strategy.items():
                pct = (count / len(open_positions) * 100) if open_positions else 0
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                    <span>{strategy}</span>
                    <span><strong>{count}</strong> ({pct:.0f}%)</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No positions")

    # Quick actions - compact row
    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔍 Scan Opportunities", use_container_width=True):
            st.switch_page("pages/2_scanner.py")

    with col2:
        if st.button("➕ Add Position", use_container_width=True):
            st.switch_page("pages/4_positions.py")

    with col3:
        if st.button("💡 View Suggestions", use_container_width=True):
            st.switch_page("pages/5_suggestions.py")

    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.switch_page("pages/6_settings.py")


# Run the page
render_dashboard()
