"""
Suggestions Page - Position-based recommendations.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime

from database import DatabaseManager, init_database


def render_suggestions():
    """Render the suggestions page."""
    st.title("💡 Suggestions")
    st.markdown("Smart recommendations based on your positions")

    # Initialize database
    init_database()

    # Get open positions
    positions = DatabaseManager.get_open_positions()

    if not positions:
        st.info("No open positions. Add positions to get personalized suggestions.")
        return

    # Categorize positions by urgency
    expiring_critical = [p for p in positions if p.days_to_expiry <= 3]
    expiring_soon = [p for p in positions if 3 < p.days_to_expiry <= 7]
    approaching = [p for p in positions if 7 < p.days_to_expiry <= 14]
    stable = [p for p in positions if p.days_to_expiry > 14]

    # Summary cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🔴 Critical",
            len(expiring_critical),
            help="Expiring in 3 days or less"
        )

    with col2:
        st.metric(
            "🟠 Expiring Soon",
            len(expiring_soon),
            help="Expiring in 4-7 days"
        )

    with col3:
        st.metric(
            "🟡 Approaching",
            len(approaching),
            help="Expiring in 8-14 days"
        )

    with col4:
        st.metric(
            "🟢 Stable",
            len(stable),
            help="More than 14 days to expiry"
        )

    st.markdown("---")

    # Critical alerts
    if expiring_critical:
        st.error("### 🚨 Critical: Action Required!")

        for pos in expiring_critical:
            with st.expander(
                f"**{pos.underlying}** ${pos.strike} {pos.option_type} - "
                f"Expires in {pos.days_to_expiry} day(s)",
                expanded=True
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Strategy:** {pos.strategy_type}")
                    st.markdown(f"**Premium Collected:** ${pos.premium_collected:.2f}")
                    st.markdown(f"**Expiry:** {pos.expiry.strftime('%Y-%m-%d') if pos.expiry else 'N/A'}")

                    st.markdown("---")
                    st.markdown("#### Recommended Actions:")

                    if pos.option_type == "PUT":
                        st.markdown("""
                        1. **Let Expire (if OTM):** If the stock price is above your strike, let it expire worthless for full profit.
                        2. **Roll Out:** If ITM or close, consider rolling to next week/month for more premium.
                        3. **Close Position:** Buy back the option if you want to exit.
                        4. **Take Assignment:** If you're happy owning the stock at this price, let it assign.
                        """)
                    else:
                        st.markdown("""
                        1. **Let Expire (if OTM):** If stock is below strike, keep the premium.
                        2. **Roll Out:** Roll to a later expiration to collect more premium.
                        3. **Close Position:** Buy back if you want to keep the shares.
                        """)

                with col2:
                    st.markdown("#### Quick Actions")
                    if st.button(f"🔄 Find Roll Options", key=f"roll_{pos.id}"):
                        st.info("Connect to IBKR to find roll opportunities")

                    if st.button(f"✅ Mark Closed", key=f"close_{pos.id}"):
                        st.session_state[f"close_dialog_{pos.id}"] = True

    # Expiring soon
    if expiring_soon:
        st.warning("### ⚠️ Expiring This Week")

        for pos in expiring_soon:
            with st.expander(
                f"{pos.underlying} ${pos.strike} {pos.option_type} - "
                f"{pos.days_to_expiry} days to expiry"
            ):
                st.markdown(f"""
                **Premium:** ${pos.premium_collected:.2f} |
                **Strategy:** {pos.strategy_type} |
                **DTE:** {pos.days_to_expiry}

                **Suggestion:** Start planning your exit. Consider rolling if you want to continue the position.
                """)

    # Roll opportunities
    st.markdown("---")
    st.subheader("🔄 Roll Opportunities")

    if not st.session_state.get('ibkr_connected', False):
        st.info("Connect to IBKR to see live roll opportunities with pricing.")

        # Show example
        with st.expander("Example Roll Analysis"):
            st.markdown("""
            **Current Position:** AAPL $180 Put, 3 DTE, $0.50 remaining value

            **Roll Options:**
            | Expiry | Strike | Premium | Net Credit | DTE |
            |--------|--------|---------|------------|-----|
            | Feb 23 | $180   | $2.15   | $1.65      | 10  |
            | Feb 23 | $175   | $1.25   | $0.75      | 10  |
            | Mar 01 | $180   | $3.45   | $2.95      | 17  |
            | Mar 01 | $175   | $2.20   | $1.70      | 17  |

            **Recommendation:** Roll to Mar 01 $180 for $2.95 credit (best risk-adjusted return)
            """)
    else:
        for pos in positions:
            if pos.days_to_expiry <= 14:
                st.write(f"Analyzing roll options for {pos.underlying}...")

    # Covered Call opportunities (for assigned puts)
    st.markdown("---")
    st.subheader("📈 Post-Assignment Ideas")

    assigned = [p for p in DatabaseManager.get_all_positions() if p.status == "ASSIGNED"]

    if assigned:
        for pos in assigned:
            st.markdown(f"""
            **{pos.underlying}** was assigned at ${pos.strike:.2f}

            **Covered Call Opportunities:**
            - Sell calls at ${pos.strike + 5:.2f} or higher to generate income
            - Consider 30-45 DTE for optimal theta decay
            """)
    else:
        st.info("When puts are assigned, covered call suggestions will appear here.")

    # Profit taking suggestions
    st.markdown("---")
    st.subheader("💰 Profit Taking")

    for pos in positions:
        # In real implementation, we'd fetch current prices
        # For now, use placeholder logic
        if pos.days_to_expiry < pos.days_to_expiry:  # Would compare to initial DTE
            st.markdown(f"""
            **{pos.underlying} ${pos.strike} {pos.option_type}**

            Consider closing early if the option has lost 50%+ of its value.
            This frees up capital for new opportunities.
            """)

    # Portfolio suggestions
    st.markdown("---")
    st.subheader("📊 Portfolio Suggestions")

    # Diversification check
    symbols = [p.underlying for p in positions]
    unique_symbols = set(symbols)

    if len(positions) > 0 and len(unique_symbols) < len(positions) * 0.5:
        st.warning(f"""
        **Concentration Warning:** You have positions in only {len(unique_symbols)} unique symbols.
        Consider diversifying across more underlyings to reduce risk.
        """)

    # Strategy mix
    strategies = [p.strategy_type for p in positions]
    strategy_counts = {}
    for s in strategies:
        strategy_counts[s] = strategy_counts.get(s, 0) + 1

    st.markdown("**Strategy Distribution:**")
    for strategy, count in strategy_counts.items():
        pct = count / len(positions) * 100
        st.markdown(f"- {strategy}: {count} positions ({pct:.0f}%)")


# Run the page
render_suggestions()
