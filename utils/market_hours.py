"""Market hours utilities for US options markets."""

from datetime import datetime, time
from typing import Tuple, Optional
import logging

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from config.constants import (
    MARKET_OPEN_HOUR,
    MARKET_OPEN_MINUTE,
    MARKET_CLOSE_HOUR,
    MARKET_CLOSE_MINUTE,
    MARKET_TIMEZONE
)

logger = logging.getLogger(__name__)

# US Market Holidays 2024-2025 (dates when market is closed)
# Format: (month, day)
US_MARKET_HOLIDAYS_2024 = [
    (1, 1),    # New Year's Day
    (1, 15),   # MLK Day
    (2, 19),   # Presidents Day
    (3, 29),   # Good Friday
    (5, 27),   # Memorial Day
    (6, 19),   # Juneteenth
    (7, 4),    # Independence Day
    (9, 2),    # Labor Day
    (11, 28),  # Thanksgiving
    (12, 25),  # Christmas
]

US_MARKET_HOLIDAYS_2025 = [
    (1, 1),    # New Year's Day
    (1, 20),   # MLK Day
    (2, 17),   # Presidents Day
    (4, 18),   # Good Friday
    (5, 26),   # Memorial Day
    (6, 19),   # Juneteenth
    (7, 4),    # Independence Day
    (9, 1),    # Labor Day
    (11, 27),  # Thanksgiving
    (12, 25),  # Christmas
]


def get_eastern_time() -> datetime:
    """Get current time in US Eastern timezone."""
    eastern = ZoneInfo(MARKET_TIMEZONE)
    return datetime.now(eastern)


def is_market_holiday(dt: Optional[datetime] = None) -> bool:
    """Check if the given date is a US market holiday."""
    if dt is None:
        dt = get_eastern_time()

    month_day = (dt.month, dt.day)
    year = dt.year

    if year == 2024:
        return month_day in US_MARKET_HOLIDAYS_2024
    elif year == 2025:
        return month_day in US_MARKET_HOLIDAYS_2025

    # For other years, just check common holidays
    return month_day in [(1, 1), (12, 25), (7, 4)]


def is_weekend(dt: Optional[datetime] = None) -> bool:
    """Check if the given date is a weekend."""
    if dt is None:
        dt = get_eastern_time()
    return dt.weekday() >= 5  # Saturday = 5, Sunday = 6


def is_market_open() -> Tuple[bool, str]:
    """
    Check if the US options market is currently open.

    Returns:
        Tuple of (is_open: bool, status_message: str)
    """
    now = get_eastern_time()

    # Check weekend
    if is_weekend(now):
        day_name = "Saturday" if now.weekday() == 5 else "Sunday"
        return False, f"Market closed - {day_name}. Opens Monday 9:30 AM ET."

    # Check holiday
    if is_market_holiday(now):
        return False, "Market closed - US market holiday."

    # Check time
    market_open = time(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE)
    market_close = time(MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE)
    current_time = now.time()

    if current_time < market_open:
        minutes_until = (
            (MARKET_OPEN_HOUR * 60 + MARKET_OPEN_MINUTE) -
            (current_time.hour * 60 + current_time.minute)
        )
        hours = minutes_until // 60
        mins = minutes_until % 60
        return False, f"Market opens in {hours}h {mins}m (9:30 AM ET)."

    if current_time >= market_close:
        return False, "Market closed for today. Opens tomorrow 9:30 AM ET."

    # Market is open
    minutes_remaining = (
        (MARKET_CLOSE_HOUR * 60 + MARKET_CLOSE_MINUTE) -
        (current_time.hour * 60 + current_time.minute)
    )
    hours = minutes_remaining // 60
    mins = minutes_remaining % 60
    return True, f"Market open - {hours}h {mins}m until close (4:00 PM ET)."


def get_market_status_display() -> dict:
    """
    Get market status for UI display.

    Returns:
        dict with keys: is_open, message, css_class, icon
    """
    is_open, message = is_market_open()

    if is_open:
        return {
            "is_open": True,
            "message": message,
            "css_class": "text-profit",
            "icon": "🟢",
            "banner_class": "ob-banner-success"
        }
    else:
        return {
            "is_open": False,
            "message": message,
            "css_class": "text-warning",
            "icon": "🔴",
            "banner_class": "ob-banner-warning"
        }


def get_next_market_open() -> str:
    """Get a human-readable string for when the market next opens."""
    now = get_eastern_time()

    # If it's a weekday and before close, market opens today or is open
    if now.weekday() < 5:
        if now.time() < time(MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE):
            if now.time() < time(MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE):
                return "Today at 9:30 AM ET"
            else:
                return "Open now"

    # Find next trading day
    days_ahead = 1
    if now.weekday() == 4:  # Friday after close
        days_ahead = 3
    elif now.weekday() == 5:  # Saturday
        days_ahead = 2
    elif now.weekday() == 6:  # Sunday
        days_ahead = 1

    return f"Next trading day at 9:30 AM ET"
