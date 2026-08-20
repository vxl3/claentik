"""Authorization helpers (owner/admin checks)."""
from __future__ import annotations

from app.config.settings import get_settings
from app.models.user import User, UserRole


def is_owner(user: User | None) -> bool:
    """Whether the user is the configured owner."""
    if user is None:
        return False
    return user.telegram_id == get_settings().owner_telegram_id


def is_admin(user: User | None) -> bool:
    """Whether the user has admin-level privileges (owner or admin role)."""
    if user is None:
        return False
    return is_owner(user) or user.role == UserRole.ADMIN


def is_blocked(user: User | None) -> bool:
    return user is not None and user.role == UserRole.BLOCKED
