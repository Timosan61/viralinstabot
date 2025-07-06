"""Formatting utilities."""

from datetime import datetime
from typing import Union


def format_number(num: Union[int, float]) -> str:
    """Format number with thousand separators."""
    if isinstance(num, float):
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return f"{num:.1f}"
    else:
        if num >= 1000000:
            return f"{num/1000000:.0f}M"
        elif num >= 1000:
            return f"{num/1000:.0f}K"
        else:
            return str(num)


def format_currency(amount: float, currency: str = "₽") -> str:
    """Format currency amount."""
    return f"{amount:,.0f} {currency}"


def format_datetime(dt: datetime) -> str:
    """Format datetime to readable string."""
    return dt.strftime("%d.%m.%Y %H:%M")


def format_engagement_rate(er: float) -> str:
    """Format engagement rate."""
    return f"{er:.1f}%"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value:.1f}%"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds}с"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}м"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}ч {minutes}м"