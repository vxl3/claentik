"""Centralized Arabic user-facing strings and message builders.

Keeping all copy in one place makes the interface consistent and easy to
maintain.
"""
from __future__ import annotations

from app.utils.formatting import format_duration, format_number

SEPARATOR = "━━━━━━━━━━━━━━━━━━"

MAIN_MENU = (
    "👋 أهلاً بك في بوت إدارة TikTok\n\n"
    "اختر العملية من الأزرار بالأسفل:"
)

HELP_TEXT = (
    "❓ <b>المساعدة</b>\n\n"
    "• <b>➕ إضافة حساب</b> — أضف حساب TikTok الخاص بك.\n"
    "• <b>🧹 تنظيف Following</b> — ألغِ متابعة من لا يتابعك.\n"
    "• <b>🗑️ تنظيف Followers</b> — أزل من يتابعك وأنت لا تتابعه.\n"
    "• <b>👤 حساباتي</b> — إدارة حساباتك المتعددة.\n\n"
    "الأوامر: /start /help /settings /accounts /cancel"
)


def account_stats(account) -> str:
    return (
        f"{SEPARATOR}\n"
        f"📊 <b>إحصائيات الحساب</b>\n"
        f"👤 الحساب: @{account.username}\n"
        f"👥 المتابعون: {format_number(account.followers_count)}\n"
        f"➡️ المتابَعون: {format_number(account.following_count)}\n"
        f"{SEPARATOR}"
    )


def plan_message(account, unfollow_count: int, remove_count: int) -> str:
    return (
        f"{account_stats(account)}\n"
        f"🧹 سيتم إلغاء متابعة: {format_number(unfollow_count)} حساب\n"
        f"🗑️ سيتم إزالة: {format_number(remove_count)} حساب\n"
        f"{SEPARATOR}"
    )


def progress_message(
    operation_type_label: str,
    processed: int,
    total: int,
    success: int,
    failed: int,
) -> str:
    return (
        f"🧹 <b>جاري تنظيف {operation_type_label}</b>\n"
        f"{SEPARATOR}\n"
        f"📊 <b>التقدم</b>\n"
        f"تمت المعالجة: {format_number(processed)} / {format_number(total)}\n"
        f"نجحت: {format_number(success)}\n"
        f"فشلت: {format_number(failed)}\n"
        f"{SEPARATOR}\n"
        f"⏳ العملية مستمرة..."
    )


def result_message(
    operation_type_label: str,
    total: int,
    success: int,
    failed: int,
    duration: float | None,
) -> str:
    return (
        f"✅ <b>اكتملت العملية</b>\n"
        f"{SEPARATOR}\n"
        f"📊 <b>النتيجة</b>\n"
        f"إجمالي الحسابات: {format_number(total)}\n"
        f"✅ نجحت: {format_number(success)}\n"
        f"❌ فشلت: {format_number(failed)}\n"
        f"⏱️ مدة التنفيذ: {format_duration(duration)}\n"
        f"{SEPARATOR}"
    )


def stopped_message(
    processed: int,
    total: int,
    success: int,
    failed: int,
) -> str:
    return (
        f"⛔ <b>تم إيقاف العملية</b>\n"
        f"{SEPARATOR}\n"
        f"📊 تمت معالجة: {format_number(processed)} / {format_number(total)}\n"
        f"✅ نجحت: {format_number(success)}\n"
        f"❌ فشلت: {format_number(failed)}\n"
        f"{SEPARATOR}"
    )


def owner_stats_message(data: dict) -> str:
    return (
        f"📊 <b>إحصائيات النظام</b>\n"
        f"{SEPARATOR}\n"
        f"👥 إجمالي المستخدمين: {format_number(data.get('users', 0))}\n"
        f"🟢 المستخدمون النشطون: {format_number(data.get('active_users', 0))}\n"
        f"📱 حسابات TikTok المضافة: {format_number(data.get('accounts', 0))}\n"
        f"🧹 عمليات التنظيف: {format_number(data.get('operations', 0))}\n"
        f"✅ العمليات الناجحة: {format_number(data.get('completed', 0))}\n"
        f"❌ العمليات الفاشلة: {format_number(data.get('failed', 0))}\n"
        f"🚫 المستخدمون المحظورون: {format_number(data.get('blocked', 0))}\n"
        f"{SEPARATOR}"
    )
