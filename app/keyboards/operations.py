"""Operation-related inline keyboards."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot import callbacks as cb


def start_plan(operation_key: str) -> InlineKeyboardMarkup:
    """Start/cancel buttons shown after the statistics preview."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🧹 بدء التنظيف", callback_data=f"{cb.CB_OP_START}{operation_key}"
        ),
        InlineKeyboardButton(text="❌ إلغاء", callback_data=cb.CB_OP_CANCEL_PLAN),
    )
    return builder.as_markup()


def stop_operation(account_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⛔ إيقاف العملية", callback_data=f"{cb.CB_OP_STOP}{account_id}"
        ),
    )
    return builder.as_markup()
