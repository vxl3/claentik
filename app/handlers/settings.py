"""Settings handler (read-only overview of pacing / runtime config)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot import callbacks as cb
from app.config.pacing import build_pacing_config
from app.keyboards.main import back_to_menu

router = Router(name="settings")


def _settings_text() -> str:
    p = build_pacing_config()
    return (
        "⚙️ <b>الإعدادات</b>\n\n"
        "⏱️ الفواصل الزمنية بين العمليات (محافظة لتقليل الضغط على TikTok):\n"
        f"• التأخير الأساسي: {p.base_delay_seconds} ثانية\n"
        f"• تأرجح عشوائي: {p.jitter_min}–{p.jitter_max} ثانية\n"
        f"• أقصى تأخير عند الازدحام: {p.backoff_max_seconds} ثانية\n"
        f"• حد الأخطاء المتتالية قبل التوقف: {p.max_consecutive_failures}\n\n"
        "هذه القيم قابلة للتعديل من ملف الإعدادات (دون تعديل منطق البوت)."
    )


@router.callback_query(F.data == cb.CB_SETTINGS)
async def on_settings(query: CallbackQuery) -> None:
    await query.message.edit_text(_settings_text(), reply_markup=back_to_menu())
    await query.answer()


async def show_settings(message: Message) -> None:
    await message.answer(_settings_text(), reply_markup=back_to_menu())
