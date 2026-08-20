"""Owner/admin panel handlers."""
from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot import callbacks as cb
from app.bot.states import BroadcastState
from app.database.engine import session_scope
from app.keyboards.owner import owner_panel
from app.models.user import User
from app.repositories.account_repository import AccountRepository
from app.repositories.admin_log_repository import AdminLogRepository
from app.repositories.user_repository import UserRepository
from app.security.access import is_admin
from app.services.broadcast_service import broadcast
from app.services.stats_service import owner_stats
from app.utils.text import owner_stats_message

router = Router(name="owner")


async def _require_admin(query: CallbackQuery, user: User) -> bool:
    if not is_admin(user):
        await query.answer("⛔ غير مصرح لك.", show_alert=True)
        return False
    return True


@router.callback_query(F.data == cb.CB_OWNER_PANEL)
async def on_owner_panel(query: CallbackQuery, user: User) -> None:
    if not await _require_admin(query, user):
        return
    await query.message.edit_text(
        "⚙️ <b>لوحة الإدارة</b>\n\nاختر القسم:", reply_markup=owner_panel()
    )
    await query.answer()


@router.callback_query(F.data == cb.CB_OWNER_STATS)
async def on_owner_stats(query: CallbackQuery, user: User) -> None:
    if not await _require_admin(query, user):
        return
    data = await owner_stats()
    await query.message.edit_text(owner_stats_message(data), reply_markup=owner_panel())
    await query.answer()


@router.callback_query(F.data == cb.CB_OWNER_USERS)
async def on_owner_users(query: CallbackQuery, user: User) -> None:
    if not await _require_admin(query, user):
        return
    async with session_scope() as session:
        users = await UserRepository(session).list_recent(50)
    lines = ["👥 <b>أحدث المستخدمين</b>\n"]
    for u in users:
        name = u.first_name or "—"
        uname = f"@{u.username}" if u.username else ""
        lines.append(f"• {name} {uname} ({u.telegram_id})")
    await query.message.edit_text("\n".join(lines), reply_markup=owner_panel())
    await query.answer()


@router.callback_query(F.data == cb.CB_OWNER_ACCOUNTS)
async def on_owner_accounts(query: CallbackQuery, user: User) -> None:
    if not await _require_admin(query, user):
        return
    async with session_scope() as session:
        accounts = await AccountRepository(session).list_recent(50)
    lines = ["📱 <b>أحدث حسابات TikTok</b>\n"]
    for a in accounts:
        lines.append(f"• @{a.username} (user: {a.user_id})")
    await query.message.edit_text("\n".join(lines), reply_markup=owner_panel())
    await query.answer()


@router.callback_query(F.data == cb.CB_OWNER_BLOCKED)
async def on_owner_blocked(query: CallbackQuery, user: User) -> None:
    if not await _require_admin(query, user):
        return
    async with session_scope() as session:
        blocked = await UserRepository(session).list_blocked()
    if not blocked:
        text = "🚫 لا يوجد مستخدمون محظورون."
    else:
        lines = ["🚫 <b>المستخدمون المحظورون</b>\n"]
        for u in blocked:
            uname = f"@{u.username}" if u.username else u.telegram_id
            lines.append(f"• {uname}")
        text = "\n".join(lines)
    await query.message.edit_text(text, reply_markup=owner_panel())
    await query.answer()


@router.callback_query(F.data == cb.CB_OWNER_BROADCAST)
async def on_broadcast_start(query: CallbackQuery, state: FSMContext, user: User) -> None:
    if not await _require_admin(query, user):
        return
    await query.message.edit_text("📢 أرسل نص الرسالة التي تريد بثّها لجميع المستخدمين:")
    await state.set_state(BroadcastState.waiting_text)
    await query.answer()


@router.message(BroadcastState.waiting_text)
async def on_broadcast_text(message: Message, state: FSMContext, user: User) -> None:
    if not is_admin(user):
        await state.clear()
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer("⚠️ الرسالة فارغة. أرسل نصًا صالحًا.")
        return
    await state.clear()

    status_msg = await message.answer("📢 جاري الإرسال للمستخدمين...")

    async def _run() -> None:
        result = await broadcast(message.bot, text)
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=(
                "📢 <b>نتيجة البث</b>\n\n"
                f"عدد المستلمين: {result['total']}\n"
                f"الناجحين: {result['success']}\n"
                f"الفاشلين: {result['failed']}"
            ),
        )

    asyncio.create_task(_run())


@router.callback_query(F.data == cb.CB_OWNER_LOGS)
async def on_owner_logs(query: CallbackQuery, user: User) -> None:
    if not await _require_admin(query, user):
        return
    async with session_scope() as session:
        logs = await AdminLogRepository(session).latest(20)
    if not logs:
        text = "📜 لا توجد سجلات."
    else:
        lines = ["📜 <b>أحدث السجلات</b>\n"]
        for log in logs:
            lines.append(
                f"• [{log.created_at.strftime('%H:%M')}] {log.action} (actor {log.actor_id})"
            )
        text = "\n".join(lines)
    await query.message.edit_text(text, reply_markup=owner_panel())
    await query.answer()


@router.callback_query(F.data == cb.CB_OWNER_SETTINGS)
async def on_owner_settings(query: CallbackQuery, user: User) -> None:
    if not await _require_admin(query, user):
        return
    from app.config.settings import get_settings

    s = get_settings()
    text = (
        "⚙️ <b>إعدادات النظام</b>\n\n"
        f"• أتمتة TikTok: {'مفعّلة' if s.tiktok_automation_enabled else 'معطلة'}\n"
        f"• المتصفح headless: {'نعم' if s.tiktok_browser_headless else 'لا'}\n"
        f"• حفظ الجلسة: {'نعم' if s.tiktok_persist_session else 'لا (موصى به)'}\n"
        f"• حجم دفعة البث: {s.broadcast_batch_size}\n"
    )
    await query.message.edit_text(text, reply_markup=owner_panel())
    await query.answer()
