"""Input validation helpers.

No user input is trusted. Every value crossing from Telegram into the system
is validated here.
"""
from __future__ import annotations

import re

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{1,64}$")
OTP_RE = re.compile(r"^\d{4,8}$")


def validate_tiktok_username(value: str) -> str | None:
    """Return a normalized username or None if invalid."""
    if not value:
        return None
    username = value.strip().lstrip("@").lower()
    if not USERNAME_RE.match(username):
        return None
    return username


def validate_otp(value: str) -> str | None:
    """Return a normalized OTP or None if invalid."""
    if not value:
        return None
    code = value.strip().replace(" ", "")
    if not OTP_RE.match(code):
        return None
    return code


def validate_login_identifier(value: str) -> str | None:
    """Validate an email or phone identifier (lenient but bounded)."""
    if not value:
        return None
    value = value.strip()
    if len(value) > 128:
        return None
    if not re.match(r"^[A-Za-z0-9@.+_\- ]+$", value):
        return None
    return value


def validate_password(value: str) -> str | None:
    """Password is only validated for length; never logged or stored."""
    if not value:
        return None
    if len(value) > 256:
        return None
    return value


def validate_broadcast_text(value: str) -> str | None:
    if not value or not value.strip():
        return None
    if len(value) > 4096:
        return None
    return value.strip()
