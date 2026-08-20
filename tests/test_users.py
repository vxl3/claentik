"""Tests for user creation and management."""
from __future__ import annotations

from app.models.user import UserRole
from app.services.user_service import get_or_create_user


async def test_get_or_create_creates_new_user():
    user, created = await get_or_create_user(
        12345, username="testuser", first_name="Test"
    )
    assert created is True
    assert user.telegram_id == 12345
    assert user.username == "testuser"
    assert user.role == UserRole.USER


async def test_get_or_create_returns_existing():
    _, created1 = await get_or_create_user(999, username="a", first_name="A")
    user2, created2 = await get_or_create_user(999, username="a", first_name="A")
    assert created1 is True
    assert created2 is False
    assert user2.telegram_id == 999


async def test_set_role():
    from app.services.user_service import set_user_role

    await get_or_create_user(555)
    await set_user_role(555, UserRole.OWNER)
    user, _ = await get_or_create_user(555)
    assert user.role == UserRole.OWNER
