"""User-facing statistics handler."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot import callbacks as cb
from app.keyboards.main import back_to_menu
from app.models.user import User
from app.services.account_service import list_accounts
from app.utils.formatting import format_number
from app.utils.text import SEPARATOR

router = Router(name="stats")


@router.callback_query(F.data == cb.CB_STATS)
async def on_stats(query: CallbackQuery, user: User) -> None:
    accounts = await list_accounts(user.telegram_id)
    if not accounts:
        await query.message.edit_text(
            "📊 لا توجد إحصائيات بعد. أضف حساب TikTok أولًا.", reply_markup=back_to_menu()
        )
        await query.answer()
        return

    total_followers = sum(a.followers_count for a in accounts)
    total_following = sum(a.following_count for a in accounts)

    lines = [f"{SEPARATOR}", "📊 <b>إحصائياتك</b>", f"{SEPARATOR}"]
    for a in accounts:
        lines.append(
            f"👤 @{a.username}: {format_number(a.followers_count)} متابع / "
            f"{format_number(a.following_count)} متابَع"
        )
    lines.append(f"{SEPARATOR}")
    lines.append(f"👥 إجمالي المتابعين: {format_number(total_followers)}")
    lines.append(f"➡️ إجمالي المتابَعين: {format_number(total_following)}")
    lines.append(f"{SEPARATOR}")

    await query.message.edit_text("\n".join(lines), reply_markup=back_to_menu())
    await query.answer()
