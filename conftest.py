"""Shared pytest fixtures.

Sets up an isolated in-memory SQLite database for every test, wired into the
application's engine module so repositories/services under test use it.
"""
from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.database.engine as engine_mod
from app.database.base import Base
import app.models  # noqa: F401 - register models


@pytest_asyncio.fixture(autouse=True)
async def _database():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    engine_mod._engine = engine
    engine_mod._session_factory = async_sessionmaker(
        engine, expire_on_commit=False, autoflush=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    engine_mod._engine = None
    engine_mod._session_factory = None
