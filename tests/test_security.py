"""Tests for validation, access control and the temporary store."""
from __future__ import annotations

from app.security import validation
from app.security.access import is_admin, is_owner
from app.security.temp_store import TempStore
from app.models.user import User, UserRole


def test_validate_tiktok_username():
    assert validation.validate_tiktok_username("@My_User.123") == "my_user.123"
    assert validation.validate_tiktok_username("  user  ") == "user"
    assert validation.validate_tiktok_username("bad user!") is None
    assert validation.validate_tiktok_username("") is None


def test_validate_otp():
    assert validation.validate_otp("123456") == "123456"
    assert validation.validate_otp("12 34 56") == "123456"
    assert validation.validate_otp("abc") is None
    assert validation.validate_otp("") is None


def test_is_owner(monkeypatch):
    owner_id = 111
    import app.security.access as access

    monkeypatch.setattr(
        access, "get_settings", lambda: type("S", (), {"owner_telegram_id": owner_id})()
    )
    owner_user = User(telegram_id=owner_id, role=UserRole.USER)
    other_user = User(telegram_id=222, role=UserRole.USER)
    assert is_owner(owner_user) is True
    assert is_owner(other_user) is False
    assert is_owner(None) is False


def test_is_admin(monkeypatch):
    import app.security.access as access

    monkeypatch.setattr(
        access, "get_settings", lambda: type("S", (), {"owner_telegram_id": 111})()
    )
    admin_user = User(telegram_id=222, role=UserRole.ADMIN)
    assert is_admin(admin_user) is True
    assert is_admin(User(telegram_id=333, role=UserRole.USER)) is False
    assert is_admin(None) is False


def test_temp_store_ttl_and_pop():
    store = TempStore(default_ttl=0.5)
    store.put("k", "secret")
    assert store.get("k") == "secret"
    import time

    time.sleep(0.6)
    assert store.get("k") is None
    store.put("k2", "v")
    assert store.pop("k2") == "v"
    assert store.get("k2") is None
