"""Text formatting helpers for Arabic user-facing output."""
from __future__ import annotations


def format_number(value: int | float | None) -> str:
    """Format a number with thousands separators (1,250)."""
    if value is None:
        return "0"
    return f"{int(value):,}"


def format_duration(seconds: float | None) -> str:
    """Format a duration in seconds as a human readable Arabic string."""
    if seconds is None:
        return "—"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} ثانية"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes} دقيقة و{secs} ثانية"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} ساعة و{minutes} دقيقة"
