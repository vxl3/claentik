"""Tests for TikTok account management (add, list, delete, multiple)."""
from __future__ import annotations

from app.models.tiktok_account import AccountStatus
from app.services.account_service import (
    add_account,
    delete_account,
    get_account,
    list_accounts,
)


async def test_add_account():
    account = await add_account(1, "account1", tiktok_user_id="uid1", display_name="A")
    assert account.id is not None
    assert account.username == "account1"
    assert account.status == AccountStatus.CONNECTED


async def test_add_account_deduplicates():
    a1 = await add_account(1, "dup")
    a2 = await add_account(1, "dup")
    assert a1.id == a2.id


async def test_multiple_accounts():
    await add_account(1, "one")
    await add_account(1, "two")
    await add_account(1, "three")
    accounts = await list_accounts(1)
    assert len(accounts) == 3
    usernames = {a.username for a in accounts}
    assert usernames == {"one", "two", "three"}


async def test_accounts_are_isolated_per_user():
    await add_account(1, "shared_name")
    await add_account(2, "shared_name")
    assert len(await list_accounts(1)) == 1
    assert len(await list_accounts(2)) == 1


async def test_delete_account():
    account = await add_account(1, "todelete")
    assert await delete_account(account.id) is True
    assert await get_account(account.id) is None
    assert await delete_account(account.id) is False
