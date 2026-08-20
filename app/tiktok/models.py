"""Plain data structures shared across the TikTok adapter boundary."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TikTokProfile:
    """Basic profile information for a logged-in TikTok account."""

    user_id: str
    username: str
    display_name: str = ""
    followers_count: int = 0
    following_count: int = 0


@dataclass
class LoginChallenge:
    """An authentication challenge that requires the user's input.

    kind: "qr"  -> the client should expose a QR image the user scans
          "otp" -> the client should ask the user for a verification code
    """

    kind: str
    detail: str = ""


@dataclass
class ComparisonResult:
    """Result of comparing followers vs following lists."""

    followers: set[str] = field(default_factory=set)
    following: set[str] = field(default_factory=set)

    @property
    def i_follow_but_not_follow_back(self) -> list[str]:
        """Accounts I follow but who do not follow me back."""
        return sorted(self.following - self.followers)

    @property
    def they_follow_but_i_dont(self) -> list[str]:
        """Accounts who follow me but whom I do not follow back."""
        return sorted(self.followers - self.following)
