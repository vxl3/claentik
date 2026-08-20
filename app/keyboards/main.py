"""Main menu inline keyboard."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot import callbacks as cb


def main_menu(is_owner: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 حساباتي", callback_data=cb.CB_ACCOUNTS),
        InlineKeyboardButton(text="➕ إضافة حساب", callback_data=cb.CB_ADD_ACCOUNT),
    )
    builder.row(
        InlineKeyboardButton(text="🧹 تنظيف Following", callback_data=cb.CB_CLEAN_FOLLOWING),
        InlineKeyboardButton(text="🗑️ تنظيف Followers", callback_data=cb.CB_CLEAN_FOLLOWERS),
    )
    builder.row(
        InlineKeyboardButton(text="📊 الإحصائيات", callback_data=cb.CB_STATS),
        InlineKeyboardButton(text="⚙️ الإعدادات", callback_data=cb.CB_SETTINGS),
    )
    builder.row(
        InlineKeyboardButton(text="❓ المساعدة", callback_data=cb.CB_HELP),
    )
    if is_owner:
        builder.row(
            InlineKeyboardButton(text="⚙️ لوحة الإدارة", callback_data=cb.CB_OWNER_PANEL),
        )
    return builder.as_markup()


def back_to_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data=cb.CB_BACK_TO_MENU),
    )
    return builder.as_markup()
