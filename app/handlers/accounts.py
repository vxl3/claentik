"""Account management handlers: list, select, info, logout, delete."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot import callbacks as cb
from app.keyboards.accounts import (
    account_actions,
    accounts_list,
    delete_confirm,
)
from app.keyboards.main import back_to_menu
from app.models.tiktok_account import AccountStatus
from app.models.user import User
from app.services.account_service import (
    close_client,
    delete_account,
    get_account,
    list_accounts,
    update_account_status,
)
from app.utils.text import account_stats

router = Router(name="accounts")


async def show_accounts(message: Message, user: User) -> None:
    accounts = await list_accounts(user.telegram_id)
    if not accounts:
        await message.answer(
            "👤 <b>حساباتي</b>\n\nلا توجد حسابات مضافة بعد.\nأضف حساب TikTok للبدء.",
            reply_markup=back_to_menu(),
        )
        return
    await message.answer("👤 <b>حساباتي</b> — اختر حسابًا:", reply_markup=accounts_list(accounts))


@router.callback_query(F.data == cb.CB_ACCOUNTS)
async def on_accounts(query: CallbackQuery, user: User) -> None:
    accounts = await list_accounts(user.telegram_id)
    if not accounts:
        await query.message.edit_text(
            "لا توجد حسابات مضافة بعد. أضف حساب TikTok للبدء.",
            reply_markup=back_to_menu(),
        )
    else:
        await query.message.edit_text(
            "👤 <b>حساباتي</b> — اختر حسابًا:", reply_markup=accounts_list(accounts)
        )
    await query.answer()


@router.callback_query(F.data.startswith(cb.CB_ACCOUNT_SELECT))
async def on_account_select(query: CallbackQuery) -> None:
    account_id = int(query.data.removeprefix(cb.CB_ACCOUNT_SELECT))
    account = await get_account(account_id)
    if account is None:
        await query.answer("الحساب غير موجود.")
        return
    status = "🟢 متصل" if account.status == AccountStatus.CONNECTED else "⚪ غير متصل"
    await query.message.edit_text(
        f"👤 <b>@{account.username}</b>\n"
        f"الحالة: {status}\n"
        f"المتابعون: {account.followers_count:,}\n"
        f"المتابَعون: {account.following_count:,}\n\n"
        "اختر العملية:",
        reply_markup=account_actions(account.id),
    )
    await query.answer()


@router.callback_query(F.data.startswith(cb.CB_ACCOUNT_INFO))
async def on_account_info(query: CallbackQuery) -> None:
    account_id = int(query.data.removeprefix(cb.CB_ACCOUNT_INFO))
    account = await get_account(account_id)
    if account is None:
        await query.answer("الحساب غير موجود.")
        return
    await query.message.edit_text(account_stats(account), reply_markup=account_actions(account.id))
    await query.answer()


@router.callback_query(F.data.startswith(cb.CB_ACCOUNT_LOGOUT))
async def on_account_logout(query: CallbackQuery) -> None:
    account_id = int(query.data.removeprefix(cb.CB_ACCOUNT_LOGOUT))
    await close_client(account_id)
    await update_account_status(account_id, AccountStatus.DISCONNECTED)
    await query.message.edit_text(
        "🚪 تم تسجيل الخروج وحذف بيانات الجلسة المؤقتة.\n"
        "يمكنك تسجيل الدخول مرة أخرى في أي وقت.",
        reply_markup=back_to_menu(),
    )
    await query.answer()


@router.callback_query(F.data.startswith(cb.CB_ACCOUNT_DELETE))
async def on_account_delete(query: CallbackQuery) -> None:
    account_id = int(query.data.removeprefix(cb.CB_ACCOUNT_DELETE))
    account = await get_account(account_id)
    if account is None:
        await query.answer("الحساب غير موجود.")
        return
    await query.message.edit_text(
        f"🗑️ هل أنت متأكد من حذف الحساب <b>@{account.username}</b> من البوت؟\n\n"
        "سيتم حذف جميع البيانات المرتبطة به نهائيًا.",
        reply_markup=delete_confirm(account_id),
    )
    await query.answer()


@router.callback_query(F.data.startswith(cb.CB_ACCOUNT_DELETE_CONFIRM))
async def on_account_delete_confirm(query: CallbackQuery, user: User) -> None:
    account_id = int(query.data.removeprefix(cb.CB_ACCOUNT_DELETE_CONFIRM))
    deleted = await delete_account(account_id)
    if deleted:
        await query.message.edit_text(
            "✅ تم حذف الحساب وجميع بياناته المرتبطة.", reply_markup=back_to_menu()
        )
    else:
        await query.message.edit_text("⚠️ تعذر حذف الحساب.", reply_markup=back_to_menu())
    await query.answer()
