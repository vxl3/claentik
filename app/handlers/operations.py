"""Cleanup operation handlers: plan preview, start, and stop."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot import callbacks as cb
from app.keyboards.accounts import accounts_list
from app.keyboards.main import back_to_menu
from app.keyboards.operations import start_plan
from app.models.operation import OperationType
from app.models.user import User
from app.security.temp_store import temp_store
from app.services.account_service import get_account, list_accounts, update_account_stats
from app.services.operation_service import (
    account_is_busy,
    get_plan,
    start_operation,
    stop_operation,
)
from app.utils.text import plan_message

router = Router(name="operations")

_PLAN_TTL = 900.0


def _plan_key(account_id: int, op_type: OperationType) -> str:
    return f"plan:{account_id}:{op_type.value}"


def _targets_for(comparison, op_type: OperationType) -> list[str]:
    if op_type == OperationType.CLEANUP_FOLLOWING:
        return comparison.i_follow_but_not_follow_back
    return comparison.they_follow_but_i_dont


# --------------------------------------------------------------------------- #
# Routing from the main menu (no account selected)
# --------------------------------------------------------------------------- #
async def _route_cleanup(query: CallbackQuery, user: User, op_type: OperationType) -> None:
    accounts = await list_accounts(user.telegram_id)
    if not accounts:
        await query.message.edit_text(
            "⚠️ لا توجد حسابات مضافة. أضف حساب TikTok أولًا.", reply_markup=back_to_menu()
        )
        await query.answer()
        return
    if len(accounts) == 1:
        await _show_plan(query, user, accounts[0].id, op_type)
    else:
        await query.message.edit_text(
            "👤 اختر الحساب الذي تريد تنظيفه:", reply_markup=accounts_list(accounts)
        )
        await query.answer()


@router.callback_query(F.data == cb.CB_CLEAN_FOLLOWING)
async def clean_following_route(query: CallbackQuery, user: User) -> None:
    await _route_cleanup(query, user, OperationType.CLEANUP_FOLLOWING)


@router.callback_query(F.data == cb.CB_CLEAN_FOLLOWERS)
async def clean_followers_route(query: CallbackQuery, user: User) -> None:
    await _route_cleanup(query, user, OperationType.CLEANUP_FOLLOWERS)


# --------------------------------------------------------------------------- #
# Plan preview
# --------------------------------------------------------------------------- #
@router.callback_query(F.data.startswith(cb.CB_CLEAN_FOLLOWING + ":"))
async def clean_following_plan(query: CallbackQuery, user: User) -> None:
    account_id = int(query.data.rsplit(":", 1)[-1])
    await _show_plan(query, user, account_id, OperationType.CLEANUP_FOLLOWING)


@router.callback_query(F.data.startswith(cb.CB_CLEAN_FOLLOWERS + ":"))
async def clean_followers_plan(query: CallbackQuery, user: User) -> None:
    account_id = int(query.data.rsplit(":", 1)[-1])
    await _show_plan(query, user, account_id, OperationType.CLEANUP_FOLLOWERS)


async def _show_plan(
    query: CallbackQuery, user: User, account_id: int, op_type: OperationType
) -> None:
    await query.answer()

    account = await get_account(account_id)
    if account is None:
        await query.message.edit_text("⚠️ الحساب غير موجود.", reply_markup=back_to_menu())
        return

    if await account_is_busy(account_id):
        await query.message.edit_text(
            "⚠️ هذا الحساب قيد المعالجة حاليًا. انتظر حتى تنتهي العملية.",
            reply_markup=back_to_menu(),
        )
        return

    await query.message.edit_text("⏳ جاري جلب قوائم المتابعين والمتابَعين...")

    try:
        comparison = await get_plan(account_id)
    except Exception as exc:  # noqa: BLE001 - surface a friendly message
        await query.message.edit_text(
            f"⚠️ تعذر جلب البيانات: {getattr(exc, 'user_message', str(exc))}\n"
            "تأكد من تسجيل الدخول ومن اتصال الإنترنت.",
            reply_markup=back_to_menu(),
        )
        return

    await update_account_stats(
        account_id, len(comparison.followers), len(comparison.following)
    )
    account = await get_account(account_id)

    targets = _targets_for(comparison, op_type)
    if not targets:
        await query.message.edit_text(
            "✅ لا توجد حسابات للتنظيف. حسابك نظيف ومتوازن! 👌",
            reply_markup=back_to_menu(),
        )
        return

    unfollow_count = len(targets) if op_type == OperationType.CLEANUP_FOLLOWING else 0
    remove_count = len(targets) if op_type == OperationType.CLEANUP_FOLLOWERS else 0

    temp_store.put(_plan_key(account_id, op_type), targets, ttl=_PLAN_TTL)

    await query.message.edit_text(
        plan_message(account, unfollow_count, remove_count),
        reply_markup=start_plan(f"{account_id}:{op_type.value}"),
    )


# --------------------------------------------------------------------------- #
# Start / stop
# --------------------------------------------------------------------------- #
@router.callback_query(F.data.startswith(cb.CB_OP_START))
async def on_start(query: CallbackQuery, user: User) -> None:
    key = query.data.removeprefix(cb.CB_OP_START)
    account_id_str, op_value = key.split(":", 1)
    account_id = int(account_id_str)
    op_type = OperationType(op_value)

    targets = temp_store.pop(_plan_key(account_id, op_type))
    if targets is None:
        await query.answer("انتهت صلاحية الخطة. أعد الحساب من جديد.", show_alert=True)
        return

    await query.answer()
    ok, error = await start_operation(
        user_id=user.telegram_id,
        account_id=account_id,
        operation_type=op_type,
        targets=targets,
        bot=query.message.bot,
        chat_id=query.message.chat.id,
    )
    if not ok:
        await query.message.answer(error or "تعذر بدء العملية.", reply_markup=back_to_menu())


@router.callback_query(F.data.startswith(cb.CB_OP_STOP))
async def on_stop(query: CallbackQuery) -> None:
    account_id = int(query.data.removeprefix(cb.CB_OP_STOP))
    stopped = await stop_operation(account_id)
    if stopped:
        await query.answer("⛔ تم إرسال طلب الإيقاف. ستتوقف العملية بأمان.", show_alert=True)
    else:
        await query.answer("لا توجد عملية جارية لهذا الحساب.", show_alert=True)


@router.callback_query(F.data == cb.CB_OP_CANCEL_PLAN)
async def on_cancel_plan(query: CallbackQuery) -> None:
    await query.message.edit_text("تم الإلغاء.", reply_markup=back_to_menu())
    await query.answer()
