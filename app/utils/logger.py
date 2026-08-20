"""Logging setup with automatic secret redaction."""
from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from app.config.settings import get_settings

# Sensitive patterns that must never appear in logs.
_REDACTION_PATTERNS = [
    "password",
    "passwd",
    "otp",
    "verification_code",
    "token",
    "secret",
    "session",
    "cookie",
]

_SENSITIVE_KEYS = {
    "password",
    "passwd",
    "otp",
    "code",
    "verification_code",
    "token",
    "bot_token",
    "secret",
    "cookie",
    "session",
}


def _redact(record: dict) -> None:
    """Replace sensitive values in a log record with [REDACTED]."""
    message = record.get("message")
    if not isinstance(message, str):
        return

    # Redact key=value style tokens.
    lowered = message.lower()
    for key in _SENSITIVE_KEYS:
        marker = f"{key}="
        start = 0
        while True:
            idx = lowered.find(marker, start)
            if idx == -1:
                break
            end = message.find(" ", idx + len(marker))
            if end == -1:
                end = len(message)
            message = message[: idx + len(marker)] + "[REDACTED]" + message[end:]
            lowered = message.lower()
            start = idx + len(marker) + len("[REDACTED]")
    record["message"] = message


def setup_logging() -> None:
    """Configure loguru with console + rotating file sinks and redaction."""
    settings = get_settings()
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()  # remove default handler

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Console (stderr, safe for foreground runs).
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level.upper(),
        colorize=True,
        filter=_redact,
    )

    # General bot log.
    logger.add(
        log_dir / "bot.log",
        format=log_format,
        level=settings.log_level.upper(),
        rotation="10 MB",
        retention="14 days",
        encoding="utf-8",
        filter=_redact,
    )

    # Errors only.
    logger.add(
        log_dir / "errors.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        filter=_redact,
    )

    # TikTok adapter log.
    logger.add(
        log_dir / "tiktok.log",
        format=log_format,
        level=settings.log_level.upper(),
        rotation="10 MB",
        retention="14 days",
        encoding="utf-8",
        filter=lambda r: r["extra"].get("scope") == "tiktok",
    )


def tiktok_logger():
    """Return a logger bound with the tiktok scope."""
    return logger.bind(scope="tiktok")
