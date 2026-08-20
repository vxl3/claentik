"""Account management inline keyboards."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot import callbacks as cb


def accounts_list(accounts: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, account in enumerate(accounts, start=1):
        builder.row(
            InlineKeyboardButton(
                text=f"{i}. @{account.username}",
                callback_data=f"{cb.CB_ACCOUNT_SELECT}{account.id}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="➕ إضافة حساب", callback_data=cb.CB_ADD_ACCOUNT),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 رجوع", callback_data=cb.CB_BACK_TO_MENU),
    )
    return builder.as_markup()


def account_actions(account_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🧹 تنظيف Following", callback_data=f"{cb.CB_CLEAN_FOLLOWING}:{account_id}"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑️ تنظيف Followers", callback_data=f"{cb.CB_CLEAN_FOLLOWERS}:{account_id}"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 معلومات الحساب", callback_data=f"{cb.CB_ACCOUNT_INFO}{account_id}"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔄 تبديل الحساب", callback_data=cb.CB_ACCOUNTS
        ),
        InlineKeyboardButton(
            text="🚪 تسجيل الخروج", callback_data=f"{cb.CB_ACCOUNT_LOGOUT}{account_id}"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑️ حذف الحساب", callback_data=f"{cb.CB_ACCOUNT_DELETE}{account_id}"
        ),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 رجوع", callback_data=cb.CB_ACCOUNTS),
    )
    return builder.as_markup()


def delete_confirm(account_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ نعم، حذف", callback_data=f"{cb.CB_ACCOUNT_DELETE_CONFIRM}{account_id}"
        ),
        InlineKeyboardButton(
            text="❌ إلغاء", callback_data=f"{cb.CB_ACCOUNT_SELECT}{account_id}"
        ),
    )
    return builder.as_markup()


def login_method() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📷 الدخول عبر QR", callback_data=cb.CB_LOGIN_QR),
    )
    builder.row(
        InlineKeyboardButton(
            text="✉️ الدخول بالبريد/الهاتف", callback_data=cb.CB_LOGIN_CREDENTIALS
        ),
    )
    builder.row(
        InlineKeyboardButton(text="❌ إلغاء", callback_data=cb.CB_LOGIN_CANCEL),
    )
    return builder.as_markup()


def qr_login_actions() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 تحديث QR", callback_data=cb.CB_LOGIN_REFRESH_QR),
    )
    builder.row(
        InlineKeyboardButton(text="❌ إلغاء", callback_data=cb.CB_LOGIN_CANCEL),
    )
    return builder.as_markup()
