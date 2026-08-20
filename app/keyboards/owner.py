"""Owner panel inline keyboard."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot import callbacks as cb


def owner_panel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 الإحصائيات", callback_data=cb.CB_OWNER_STATS),
        InlineKeyboardButton(text="👥 المستخدمون", callback_data=cb.CB_OWNER_USERS),
    )
    builder.row(
        InlineKeyboardButton(text="📱 حسابات TikTok", callback_data=cb.CB_OWNER_ACCOUNTS),
        InlineKeyboardButton(text="🚫 المحظورون", callback_data=cb.CB_OWNER_BLOCKED),
    )
    builder.row(
        InlineKeyboardButton(text="📢 Broadcast", callback_data=cb.CB_OWNER_BROADCAST),
        InlineKeyboardButton(text="📜 Logs", callback_data=cb.CB_OWNER_LOGS),
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ إعدادات النظام", callback_data=cb.CB_OWNER_SETTINGS),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 رجوع", callback_data=cb.CB_BACK_TO_MENU),
    )
    return builder.as_markup()
