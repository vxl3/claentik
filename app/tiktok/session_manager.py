"""Manages Playwright browser lifecycle and per-account isolated contexts.

The browser is shared across all accounts (efficient), but every account gets
its own isolated BrowserContext so sessions and cookies never mix.

Playwright is imported lazily so the bot can start and serve its core features
(menus, accounts, owner panel, ...) even on platforms where Playwright is not
available (e.g. Android/Termux). Browser automation is only attempted when a
login/cleanup action is actually requested, and fails with a clear message if
Playwright is missing.
"""
from __future__ import annotations

import asyncio

from loguru import logger

from app.config.settings import get_settings

_playwright = None
_browser = None
_lock = asyncio.Lock()
_client_count = 0


class PlaywrightUnavailableError(RuntimeError):
    """Raised when browser automation is requested but Playwright is missing."""

    def __init__(self) -> None:
        super().__init__(
            "أتمتة TikTok غير متاحة على هذا الجهاز (متصفح Chromium غير مدعوم هنا). "
            "هذه الميزة تتطلب التشغيل على سيرفر أو كمبيوتر."
        )


def _import_playwright():
    """Import the playwright async API on demand."""
    from playwright.async_api import async_playwright  # noqa: PLC0415

    return async_playwright


async def _ensure_browser():
    """Start Playwright and launch Chromium once."""
    global _playwright, _browser
    if _browser is not None:
        return _browser
    try:
        async_playwright = _import_playwright()
    except ImportError as exc:
        raise PlaywrightUnavailableError() from exc
    settings = get_settings()
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(
        headless=settings.tiktok_browser_headless,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    logger.info("Playwright Chromium launched (headless={})", settings.tiktok_browser_headless)
    return _browser


async def new_context():
    """Create a fresh, isolated browser context for one account."""
    browser = await _ensure_browser()
    context = await browser.new_context(
        viewport={"width": 1280, "height": 900},
        locale="en-US",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
    )
    global _client_count
    _client_count += 1
    return context


async def release_context(context) -> None:
    """Close a context and release resources."""
    global _client_count
    try:
        await context.close()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Error closing browser context: {}", exc)
    finally:
        _client_count = max(0, _client_count - 1)


async def shutdown() -> None:
    """Stop the browser and Playwright (call on bot shutdown)."""
    global _browser, _playwright
    if _browser is not None:
        await _browser.close()
        _browser = None
    if _playwright is not None:
        await _playwright.stop()
        _playwright = None
    logger.info("Playwright shut down")
