"""Progress reporter — edits a single Telegram message to avoid spam."""
from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger


class ProgressReporter:
    """Edits one Telegram message periodically during an operation.

    The bot never sends a new message per action; it updates the same message.
    """

    def __init__(self, bot: Bot, chat_id: int, message_id: int) -> None:
        self._bot = bot
        self._chat_id = chat_id
        self._message_id = message_id

    async def update(self, text: str, keyboard=None) -> None:
        try:
            await self._bot.edit_message_text(
                chat_id=self._chat_id,
                message_id=self._message_id,
                text=text,
                reply_markup=keyboard,
            )
        except TelegramAPIError as exc:
            # "message is not modified" is harmless; log others.
            if "not modified" not in str(exc).lower():
                logger.warning("Progress update failed: {}", exc)

    async def finalize(self, text: str, keyboard=None) -> None:
        try:
            await self._bot.edit_message_text(
                chat_id=self._chat_id,
                message_id=self._message_id,
                text=text,
                reply_markup=keyboard,
            )
        except TelegramAPIError as exc:
            if "not modified" not in str(exc).lower():
                # Fall back to sending a new message if editing fails.
                await self._bot.send_message(
                    chat_id=self._chat_id, text=text, reply_markup=keyboard
                )
