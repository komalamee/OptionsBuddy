"""
Dashboard Page - Portfolio overview and alerts.
"""

import streamlit as st
from datetime import date, timedelta

from database import DatabaseManager, init_database
from config.constants import STATUS_OPEN


def render_dashboard():
    """Render the dashboard page."""
    st.title("🏠 Dashboard")
    st.markdown("Portfolio overview and daily alerts")

    # Initialize database
    init_database()

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    # Get position statistics
    open_positions = DatabaseManager.get_open_positions()
    stats = DatabaseManager.get_position_stats()
    total_premium = DatabaseManager.calculate_total_premium_collected()
    open_premium = DatabaseManager.calculate_open_premium()

    with col1:
        st.metric(
            label="Open Positions",
            value=len(open_positions)
        )

    with col2:
        st.metric(
            label="Total Premium",
            value=f"${total_premium:,.2f}"
        )

    with col3:
        st.metric(
            label="Open Premium",
            value=f"${open_premium:,.2f}"
        )

    with col4:
        win_rate = stats.get('win_rate', 0)
        st.metric(
            label="Win Rate",
            value=f"{win_rate:.1f}%"
        )

    st.markdown("---")

    # Two columns: Positions and Alerts
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📋 Open Positions")

        if open_positions:
            # Create a simple table
            position_data = []
            for pos in open_positions:
                dte = pos.days_to_expiry
                status_emoji = "🟢" if dte > 7 else ("🟡" if dte > 3 else "🔴")

                position_data.append({
                    "Status": status_emoji,
                    "Symbol": pos.underlying,
                    "Type": pos.option_type,
                    "Strike": f"${pos.strike:.2f}",
                    "Expiry": pos.expiry.strftime("%Y-%m-%d") if pos.expiry else "N/A",
                    "DTE": dte,
                    "Premium": f"${pos.premium_collected:.2f}",
                    "Strategy": pos.strategy_type
                })

            st.dataframe(
                position_data,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No open positions. Go to Scanner to find opportunities!")

    with col_right:
        st.subheader("⚠️ Alerts")

        # Check for positions needing attention
        expiring_soon = DatabaseManager.get_positions_near_expiry(days=7)

        if expiring_soon:
            for pos in expiring_soon:
                dte = pos.days_to_expiry
                if dte <= 3:
                    st.error(f"🔴 {pos.underlying} ${pos.strike} {pos.option_type} expires in {dte} days!")
                else:
                    st.warning(f"🟡 {pos.underlying} ${pos.strike} {pos.option_type} expires in {dte} days")
        else:
            st.success("✅ No immediate alerts")

        st.markdown("---")

        # Quick stats by strategy
        st.subheader("📊 By Strategy")
        by_strategy = stats.get('by_strategy', {})
        if by_strategy:
            for strategy, count in by_strategy.items():
                st.write(f"**{strategy}**: {count}")
        else:
            st.write("No positions yet")

    st.markdown("---")

    # Connection status and quick actions
    st.subheader("🔗 Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Scan for Opportunities", use_container_width=True):
            st.switch_page("pages/2_scanner.py")

    with col2:
        if st.button("➕ Add Position", use_container_width=True):
            st.switch_page("pages/4_positions.py")

    with col3:
        if st.button("⚙️ Settings", use_container_width=True):
            st.switch_page("pages/6_settings.py")


# Run the page
render_dashboard()
