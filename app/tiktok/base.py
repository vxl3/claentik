"""Abstract interface for a TikTok client.

The rest of the bot depends only on this interface, never on a concrete
implementation. This lets us swap the adapter (e.g. a future official API)
without touching handlers or services.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.tiktok.models import ComparisonResult, LoginChallenge, TikTokProfile


class TikTokClient(ABC):
    """Contract every TikTok integration must fulfil."""

    @abstractmethod
    async def start_login(self, mode: str = "qr") -> LoginChallenge | TikTokProfile:
        """Begin the login flow.

        ``mode`` is ``"qr"`` or ``"credentials"``. Returns a challenge that
        requires user input (QR scan or OTP) or a profile on immediate success.
        """

    @abstractmethod
    async def set_credentials(self, identifier: str, password: str) -> None:
        """(credentials mode only) Register the account identifier + password
        in memory so they can be submitted to TikTok. The password is never
        logged or persisted."""

    @abstractmethod
    async def get_qr_image(self) -> bytes:
        """(qr mode only) Return the current QR image as PNG bytes."""

    @abstractmethod
    async def wait_for_login(self, timeout: float = 180.0) -> TikTokProfile:
        """(qr mode only) Block until the user scans the QR and the session is
        established, or timeout."""

    @abstractmethod
    async def submit_otp(self, code: str) -> TikTokProfile:
        """Submit a verification code and return the profile on success."""

    @abstractmethod
    async def get_profile(self) -> TikTokProfile:
        """Fetch the profile of the currently logged-in account."""

    @abstractmethod
    async def get_followers(self) -> list[str]:
        """Fetch the list of usernames who follow this account."""

    @abstractmethod
    async def get_following(self) -> list[str]:
        """Fetch the list of usernames this account follows."""

    @abstractmethod
    async def compare(self) -> ComparisonResult:
        """Compare followers/following and return the difference sets."""

    @abstractmethod
    async def unfollow(self, username: str) -> None:
        """Unfollow a single account."""

    @abstractmethod
    async def remove_follower(self, username: str) -> None:
        """Remove a follower (implemented as blocking the account)."""

    @abstractmethod
    async def close(self) -> None:
        """Release all resources (browser context) and drop the session."""
