"""Domain-specific exceptions raised by the TikTok adapter layer."""
from __future__ import annotations


class TikTokError(Exception):
    """Base class for all TikTok adapter errors."""

    user_message: str = "حدث خطأ غير متوقع في TikTok."


class TikTokAuthError(TikTokError):
    """Authentication failed (wrong credentials, expired session, ...)."""

    user_message = "فشل تسجيل الدخول إلى TikTok. تحقق من بياناتك وأعد المحاولة."


class TikTokOtpError(TikTokError):
    """The OTP / verification code was wrong or expired."""

    user_message = "رمز التحقق غير صحيح أو انتهت صلاحيته."


class TikTokOtpTimeoutError(TikTokError):
    """The user did not provide the OTP within the allowed time."""

    user_message = "انتهت مهلة إدخال رمز التحقق."


class TikTokRateLimitError(TikTokError):
    """TikTok is throttling or blocking our actions."""

    user_message = "TikTok يحدّ من العمليات حاليًا. تم إيقاف العملية بأمان."


class TikTokAccountUnavailableError(TikTokError):
    """The account is unavailable (banned, deleted, or unreachable)."""

    user_message = "الحساب غير متاح حاليًا."


class TikTokTimeoutError(TikTokError):
    """A network request to TikTok timed out."""

    user_message = "انقطعت الشبكة أو استغرق TikTok وقتًا طويلًا في الرد."


class TikTokLoggedOutError(TikTokError):
    """The session was logged out (or expired) mid-operation."""

    user_message = "تم تسجيل الخروج من حساب TikTok. أعد تسجيل الدخول."


class TikTokActionBlockedError(TikTokError):
    """TikTok blocked a specific action (rate limit on the action itself)."""

    user_message = "TikTok يمنع هذه العملية حاليًا. تم إيقاف العملية بأمان."
