"""Unofficial TikTok integration via browser automation (Playwright).

IMPORTANT — honest disclosure
-----------------------------
TikTok does not provide an official public API for reading a user's
followers/following lists or for performing follow/unfollow/block actions on
their behalf. This adapter drives the TikTok website through a browser using
the user's own logged-in session. It is therefore **unofficial** and violates
TikTok's Terms of Service; heavy use may lead to account restriction or ban.

This implementation:
  * only manages the account the user logged into themselves,
  * performs actions sequentially with conservative pacing (handled by the
    operation layer, not here),
  * does NOT bypass CAPTCHAs, rate limits or any protection systems,
  * stops immediately when TikTok signals a restriction.

The CSS selectors below target TikTok's current web UI. TikTok changes its DOM
frequently, so these selectors may need periodic review — they are isolated at
the top of this file for that purpose.
"""
from __future__ import annotations

import asyncio
import time
from urllib.parse import quote

from playwright.async_api import BrowserContext, Error as PlaywrightError, Page

from app.tiktok.base import TikTokClient
from app.tiktok.errors import (
    TikTokAccountUnavailableError,
    TikTokActionBlockedError,
    TikTokAuthError,
    TikTokLoggedOutError,
    TikTokOtpError,
    TikTokRateLimitError,
    TikTokTimeoutError,
)
from app.tiktok.models import ComparisonResult, LoginChallenge, TikTokProfile

BASE_URL = "https://www.tiktok.com"
LOGIN_URL = "https://www.tiktok.com/login"
DEFAULT_TIMEOUT = 30_000
NAV_TIMEOUT = 60_000

# --- Selectors (best-effort, may need periodic review) ---
SEL_QR_OPTION = '[data-e2e="qr-code-login"], button:has-text("QR code")'
SEL_QR_IMAGE = '[data-e2e="qr-code-image"], .qr-code img, canvas'
SEL_EMAIL_TAB = '[data-e2e="email-login"], a[href*="phone-or-email"]'
SEL_PHONE_TAB = '[data-e2e="phone-login"]'
SEL_IDENTIFIER_INPUT = 'input[name="username"], input[placeholder*="phone"], input[placeholder*="email"]'
SEL_PASSWORD_INPUT = 'input[type="password"]'
SEL_LOGIN_BUTTON = 'button[type="submit"], button:has-text("Log in")'
SEL_OTP_INPUT = 'input[name="code"], input[placeholder*="code"], input[maxlength="6"]'
SEL_PROFILE_LINK = 'a[href^="/@"]'
SEL_FOLLOWING_BUTTON = 'button:has-text("Following")'
SEL_CONFIRM_BLOCK = 'button:has-text("Block")'
SEL_MORE_BUTTON = '[data-e2e="user-more"], button[aria-label="More options"]'
SEL_USERNAME_HEADER = '[data-e2e="user-title"], h1[data-e2e="user-title"]'


def _normalize_username(value: str) -> str:
    """Strip '@' and leading path segments from a username string."""
    value = value.strip()
    if "/" in value:
        value = value.rstrip("/").split("/")[-1]
    return value.lstrip("@").lower()


class PlaywrightTikTokClient(TikTokClient):
    """Drives a single logged-in TikTok session in its own browser context."""

    def __init__(self, context: BrowserContext) -> None:
        self._context = context
        self._page: Page | None = None
        self._identifier: str | None = None
        self._password: str | None = None
        self._username: str | None = None

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    async def _page_obj(self) -> Page:
        if self._page is None or self._page.is_closed():
            self._page = await self._context.new_page()
        return self._page

    async def _goto(self, url: str, timeout: int = NAV_TIMEOUT) -> Page:
        page = await self._page_obj()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        except PlaywrightError as exc:
            raise TikTokTimeoutError("تعذر الوصول إلى TikTok") from exc
        return page

    async def _is_logged_in(self) -> bool:
        page = await self._page_obj()
        await self._goto(BASE_URL)
        # When logged out, TikTok redirects to /login or shows a login prompt.
        await page.wait_for_timeout(1500)
        return "/login" not in page.url

    async def _detect_rate_limit(self) -> None:
        """Raise if the page indicates TikTok is throttling/blocking us."""
        page = await self._page_obj()
        content = ""
        try:
            content = await page.inner_text("body", timeout=3000)
        except PlaywrightError:
            return
        markers = ("too many requests", "you're tapping too fast", "try again later",
                   "action too frequent", "rate limit", "temporarily unavailable")
        if any(m in content.lower() for m in markers):
            raise TikTokRateLimitError()

    # ------------------------------------------------------------------ #
    # Login flow
    # ------------------------------------------------------------------ #
    async def start_login(self, mode: str = "qr") -> LoginChallenge | TikTokProfile:
        if mode == "qr":
            return await self._start_qr_login()
        return await self._start_credentials_login()

    async def _start_qr_login(self) -> LoginChallenge:
        page = await self._goto(LOGIN_URL)
        try:
            await page.click(SEL_QR_OPTION, timeout=DEFAULT_TIMEOUT)
        except PlaywrightError:
            # Some regions default straight to QR; ignore if not present.
            pass
        await page.wait_for_timeout(1500)
        # Ensure a QR element exists; otherwise fall back to error.
        try:
            await page.wait_for_selector(SEL_QR_IMAGE, timeout=10_000)
        except PlaywrightError as exc:
            raise TikTokAuthError("تعذر عرض رمز QR لتسجيل الدخول") from exc
        return LoginChallenge(kind="qr", detail="امسح رمز QR من تطبيق TikTok")

    async def _start_credentials_login(self) -> LoginChallenge | TikTokProfile:
        if self._identifier is None or self._password is None:
            raise TikTokAuthError("لم يتم تزويد بيانات الدخول")
        page = await self._goto(LOGIN_URL)
        try:
            await page.click(SEL_PHONE_TAB, timeout=DEFAULT_TIMEOUT)
        except PlaywrightError:
            try:
                await page.click(SEL_EMAIL_TAB, timeout=DEFAULT_TIMEOUT)
            except PlaywrightError:
                pass
        await page.wait_for_timeout(1000)
        try:
            await page.fill(SEL_IDENTIFIER_INPUT, self._identifier, timeout=DEFAULT_TIMEOUT)
            await page.fill(SEL_PASSWORD_INPUT, self._password or "", timeout=DEFAULT_TIMEOUT)
        except PlaywrightError as exc:
            raise TikTokAuthError("تعذر تعبئة بيانات الدخول") from exc
        await page.click(SEL_LOGIN_BUTTON, timeout=DEFAULT_TIMEOUT)
        await page.wait_for_timeout(3000)

        if await self._is_logged_in():
            return await self.get_profile()

        # OTP required?
        if await self._wait_for_otp_field(timeout=5.0):
            return LoginChallenge(kind="otp", detail="TikTok طلب رمز تحقق")
        raise TikTokAuthError("فشل تسجيل الدخول، تحقق من بياناتك")

    async def _wait_for_otp_field(self, timeout: float) -> bool:
        page = await self._page_obj()
        try:
            await page.wait_for_selector(SEL_OTP_INPUT, timeout=int(timeout * 1000))
            return True
        except PlaywrightError:
            return False

    async def set_credentials(self, identifier: str, password: str) -> None:
        self._identifier = identifier.strip()
        self._password = password

    async def get_qr_image(self) -> bytes:
        page = await self._page_obj()
        try:
            el = await page.wait_for_selector(SEL_QR_IMAGE, timeout=DEFAULT_TIMEOUT)
            data = await el.screenshot(type="png")
        except PlaywrightError as exc:
            raise TikTokAuthError("تعذر التقاط رمز QR") from exc
        if not data:
            raise TikTokAuthError("رمز QR فارغ")
        return data

    async def wait_for_login(self, timeout: float = 180.0) -> TikTokProfile:
        deadline = time.monotonic() + timeout
        page = await self._page_obj()
        while time.monotonic() < deadline:
            if await self._is_logged_in():
                return await self.get_profile()
            await page.wait_for_timeout(2000)
        raise TikTokAuthError("انتهت مهلة تسجيل الدخول عبر QR")

    async def submit_otp(self, code: str) -> TikTokProfile:
        page = await self._page_obj()
        if not await self._wait_for_otp_field(timeout=3.0):
            raise TikTokOtpError()
        try:
            await page.fill(SEL_OTP_INPUT, code.strip(), timeout=DEFAULT_TIMEOUT)
            await page.click(SEL_LOGIN_BUTTON, timeout=DEFAULT_TIMEOUT)
        except PlaywrightError as exc:
            raise TikTokOtpError() from exc
        await page.wait_for_timeout(4000)
        if not await self._is_logged_in():
            raise TikTokOtpError("رمز التحقق غير صحيح")
        return await self.get_profile()

    # ------------------------------------------------------------------ #
    # Profile / lists
    # ------------------------------------------------------------------ #
    async def get_profile(self) -> TikTokProfile:
        if not self._username:
            self._username = await self._detect_username()
        page = await self._page_obj()
        await self._goto(f"{BASE_URL}/@{quote(self._username)}")
        await page.wait_for_timeout(2000)

        # Detect "account unavailable" states.
        try:
            body = (await page.inner_text("body", timeout=3000)).lower()
        except PlaywrightError:
            body = ""
        if "couldn't find this account" in body or "account not found" in body:
            raise TikTokAccountUnavailableError()

        followers, following = await self._parse_counts()
        display_name = ""
        try:
            el = page.locator(SEL_USERNAME_HEADER).first
            display_name = (await el.inner_text(timeout=3000)).strip()
        except PlaywrightError:
            display_name = self._username
        return TikTokProfile(
            user_id=self._username,
            username=self._username,
            display_name=display_name,
            followers_count=followers,
            following_count=following,
        )

    async def _detect_username(self) -> str:
        page = await self._page_obj()
        await self._goto(BASE_URL)
        await page.wait_for_timeout(2000)
        # The avatar links to /@username
        try:
            href = await page.get_attribute('a[href^="/@"]', "href", timeout=5000)
            if href:
                return _normalize_username(href)
        except PlaywrightError:
            pass
        raise TikTokAuthError("تعذر تحديد اسم الحساب بعد تسجيل الدخول")

    async def _parse_counts(self) -> tuple[int, int]:
        """Parse follower/following counts from the profile page."""
        page = await self._page_obj()
        followers = following = 0
        try:
            strongs = page.locator("strong[data-e2e]")
            n = await strongs.count()
            for i in range(min(n, 4)):
                e2e = await strongs.nth(i).get_attribute("data-e2e")
                text = (await strongs.nth(i).inner_text(timeout=2000)).strip()
                value = _parse_abbreviated_count(text)
                if e2e == "followers-count":
                    followers = value
                elif e2e == "following-count":
                    following = value
        except PlaywrightError:
            pass
        return followers, following

    async def _collect_profile_links(self, url: str) -> list[str]:
        """Scroll a list page and collect unique @usernames."""
        page = await self._page_obj()
        await self._goto(url)
        await page.wait_for_timeout(2000)
        seen: set[str] = set()
        last_height = 0
        for _ in range(200):  # bounded scroll iterations
            links = page.locator(SEL_PROFILE_LINK)
            n = await links.count()
            for i in range(n):
                try:
                    href = await links.nth(i).get_attribute("href", timeout=1000)
                except PlaywrightError:
                    continue
                if href and href.startswith("/@"):
                    seen.add(_normalize_username(href))
            await page.mouse.wheel(0, 2500)
            await page.wait_for_timeout(1200)
            try:
                new_height = await page.evaluate("document.body.scrollHeight")
            except PlaywrightError:
                break
            if new_height == last_height:
                # Attempt one more wait then stop to avoid infinite loops.
                await page.wait_for_timeout(1500)
                if new_height == last_height:
                    break
            last_height = new_height
        await self._detect_rate_limit()
        return sorted(seen)

    async def get_followers(self) -> list[str]:
        if not self._username:
            self._username = await self._detect_username()
        return await self._collect_profile_links(
            f"{BASE_URL}/@{quote(self._username)}/followers"
        )

    async def get_following(self) -> list[str]:
        if not self._username:
            self._username = await self._detect_username()
        return await self._collect_profile_links(
            f"{BASE_URL}/@{quote(self._username)}/following"
        )

    async def compare(self) -> ComparisonResult:
        following, followers = await asyncio.gather(
            self.get_following(), self.get_followers()
        )
        return ComparisonResult(followers=set(followers), following=set(following))

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    async def unfollow(self, username: str) -> None:
        await self._check_logged_in()
        page = await self._page_obj()
        target = f"{BASE_URL}/@{quote(username)}"
        await self._goto(target)
        await page.wait_for_timeout(1500)
        try:
            btn = page.locator(SEL_FOLLOWING_BUTTON).first
            await btn.click(timeout=DEFAULT_TIMEOUT)
            await page.wait_for_timeout(800)
        except PlaywrightError as exc:
            await self._detect_rate_limit()
            raise TikTokActionBlockedError(f"تعذر إلغاء متابعة {username}") from exc
        await self._detect_rate_limit()

    async def remove_follower(self, username: str) -> None:
        await self._check_logged_in()
        page = await self._page_obj()
        target = f"{BASE_URL}/@{quote(username)}"
        await self._goto(target)
        await page.wait_for_timeout(1500)
        try:
            more = page.locator(SEL_MORE_BUTTON).first
            await more.click(timeout=DEFAULT_TIMEOUT)
            await page.wait_for_timeout(800)
            block = page.locator(SEL_CONFIRM_BLOCK).first
            await block.click(timeout=DEFAULT_TIMEOUT)
            await page.wait_for_timeout(800)
            # Confirm modal if present
            confirm = page.locator(SEL_CONFIRM_BLOCK).last
            try:
                await confirm.click(timeout=3000)
            except PlaywrightError:
                pass
        except PlaywrightError as exc:
            await self._detect_rate_limit()
            raise TikTokActionBlockedError(f"تعذر إزالة المتابع {username}") from exc
        await self._detect_rate_limit()

    async def _check_logged_in(self) -> None:
        if not await self._is_logged_in():
            raise TikTokLoggedOutError()

    # ------------------------------------------------------------------ #
    # Cleanup
    # ------------------------------------------------------------------ #
    async def close(self) -> None:
        self._password = None
        self._identifier = None
        if self._page is not None and not self._page.is_closed():
            await self._page.close()
        self._page = None


def _parse_abbreviated_count(text: str) -> int:
    """Parse TikTok's abbreviated counts like '1.2K', '3.4M', '980'."""
    text = text.strip().upper().replace(",", "")
    if not text:
        return 0
    try:
        if text.endswith("K"):
            return int(float(text[:-1]) * 1_000)
        if text.endswith("M"):
            return int(float(text[:-1]) * 1_000_000)
        if text.endswith("B"):
            return int(float(text[:-1]) * 1_000_000_000)
        return int(float(text))
    except ValueError:
        return 0
