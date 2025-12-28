"""Formatting utilities."""

from datetime import date, datetime
from typing import Union, Optional


def format_currency(value: float, include_sign: bool = False) -> str:
    """Format a number as currency."""
    if include_sign and value >= 0:
        return f"+${value:,.2f}"
    elif value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a decimal as percentage."""
    return f"{value * 100:.{decimals}f}%"


def format_date(d: Union[date, datetime, str], fmt: str = "%Y-%m-%d") -> str:
    """Format a date."""
    if isinstance(d, str):
        return d
    if isinstance(d, datetime):
        return d.strftime(fmt)
    if isinstance(d, date):
        return d.strftime(fmt)
    return str(d)


def format_delta(delta: float) -> str:
    """Format delta value."""
    return f"{delta:.2f}"


def format_dte(dte: int) -> str:
    """Format days to expiry with indicator."""
    if dte <= 0:
        return "Expired"
    elif dte == 1:
        return "1 day"
    else:
        return f"{dte} days"


def format_iv_hv_ratio(ratio: Optional[float]) -> str:
    """Format IV/HV ratio with indicator."""
    if ratio is None:
        return "N/A"
    if ratio >= 1.5:
        return f"{ratio:.2f} 🔥"
    elif ratio >= 1.2:
        return f"{ratio:.2f} ⬆️"
    elif ratio >= 1.0:
        return f"{ratio:.2f}"
    else:
        return f"{ratio:.2f} ⬇️"


def format_score(score: float) -> str:
    """Format opportunity score."""
    if score >= 80:
        return f"{score:.0f} 🌟"
    elif score >= 60:
        return f"{score:.0f} ✅"
    elif score >= 40:
        return f"{score:.0f} ⚡"
    else:
        return f"{score:.0f}"
