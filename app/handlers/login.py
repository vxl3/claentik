"""TikTok login flow (QR-first with credentials/OTP fallback).

Sensitive values (password, OTP) live only in memory for the duration of the
flow and are discarded immediately. Nothing sensitive is logged or persisted.
"""
from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.bot import callbacks as cb
from app.bot.states import LoginState
from app.keyboards.accounts import account_actions, login_method, qr_login_actions
from app.keyboards.main import back_to_menu
from app.models.user import User
from app.security import validation
from app.security.temp_store import temp_store
from app.services.account_service import (
    add_account,
    create_client,
    update_account_stats,
)
from app.tiktok.errors import (
    TikTokAuthError,
    TikTokOtpError,
    TikTokError,
)
from app.tiktok.models import LoginChallenge
from app.tiktok.registry import register

router = Router(name="login")

QR_TIMEOUT_SECONDS = 60
QR_MAX_ATTEMPTS = 3


def _login_client_key(user_id: int) -> str:
    return f"login_client:{user_id}"


def _login_task_key(user_id: int) -> str:
    return f"login_task:{user_id}"


# --------------------------------------------------------------------------- #
# Entry: add account
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == cb.CB_ADD_ACCOUNT)
async def add_account_start(query: CallbackQuery) -> None:
    await query.message.edit_text(
        "➕ <b>إضافة حساب TikTok</b>\n\n"
        "اختر طريقة تسجيل الدخول:\n\n"
        "📷 <b>QR</b> — الأسهل والأكثر أمانًا (امسح الرمز من تطبيق TikTok).\n"
        "✉️ <b>البريد/الهاتف</b> — أدخل بياناتك وكلمة المرور.",
        reply_markup=login_method(),
    )
    await query.answer()


@router.callback_query(F.data == cb.CB_LOGIN_CANCEL)
async def login_cancel(query: CallbackQuery, state: FSMContext) -> None:
    user = query.from_user
    await _cleanup_pending(user.id, state)
    await query.message.edit_text("تم إلغاء عملية تسجيل الدخول.", reply_markup=back_to_menu())
    await query.answer()


# --------------------------------------------------------------------------- #
# QR flow
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == cb.CB_LOGIN_QR)
async def login_qr(query: CallbackQuery, user: User) -> None:
    await query.answer()
    client = await create_client()
    # store temporarily under a login key, re-register under the real id later
    temp_store.put(_login_client_key(user.telegram_id), client, ttl=600)

    try:
        await client.start_login("qr")
        img = await client.get_qr_image()
    except TikTokError as exc:
        await _cleanup_pending(user.telegram_id, None)
        await query.message.answer(f"⚠️ {exc.user_message}", reply_markup=back_to_menu())
        return

    await query.message.answer_photo(
        photo=BufferedInputFile(img, filename="tiktok_qr.png"),
        caption="📷 امسح رمز QR من تطبيق TikTok:\n"
        "افتح TikTok ← الملف الشخصي ← ☰ ← رمز QR ← مسح",
        reply_markup=qr_login_actions(),
    )
    await query.message.answer("⏳ بانتظار المسح...")

    task = asyncio.create_task(
        _qr_wait(
            bot=query.message.bot,
            chat_id=query.message.chat.id,
            user_id=user.telegram_id,
        )
    )
    temp_store.put(_login_task_key(user.telegram_id), task, ttl=600)


@router.callback_query(F.data == cb.CB_LOGIN_REFRESH_QR)
async def login_refresh_qr(query: CallbackQuery, user: User) -> None:
    await query.answer()
    client = temp_store.get(_login_client_key(user.telegram_id))
    if client is None:
        await query.message.answer("لا توجد عملية تسجيل دخول نشطة.", reply_markup=back_to_menu())
        return
    try:
        img = await client.get_qr_image()
        await query.message.answer_photo(
            photo=BufferedInputFile(img, filename="tiktok_qr.png"),
            caption="📷 رمز QR جديد — امسحه من تطبيق TikTok:",
            reply_markup=qr_login_actions(),
        )
    except TikTokError as exc:
        await query.message.answer(f"⚠️ {exc.user_message}")


async def _qr_wait(bot, chat_id: int, user_id: int) -> None:
    client = temp_store.get(_login_client_key(user_id))
    if client is None:
        return
    for attempt in range(QR_MAX_ATTEMPTS):
        try:
            profile = await client.wait_for_login(timeout=QR_TIMEOUT_SECONDS)
            await _complete_login(bot, chat_id, user_id, profile)
            return
        except TikTokAuthError:
            # QR expired or not scanned — refresh and keep waiting.
            if attempt < QR_MAX_ATTEMPTS - 1:
                try:
                    img = await client.get_qr_image()
                    await bot.send_photo(
                        chat_id,
                        photo=BufferedInputFile(img, filename="tiktok_qr.png"),
                        caption="🔁 انتهت صلاحية الرمز السابق، امسح هذا الرمز الجديد:",
                        reply_markup=qr_login_actions(),
                    )
                except TikTokError:
                    pass
        except TikTokError as exc:
            await bot.send_message(chat_id, f"⚠️ {exc.user_message}")
            await _cleanup_pending(user_id, None)
            return
    await bot.send_message(
        chat_id, "⏱️ انتهت مهلة تسجيل الدخول عبر QR. حاول مرة أخرى.", reply_markup=back_to_menu()
    )
    await _cleanup_pending(user_id, None)


# --------------------------------------------------------------------------- #
# Credentials flow
# --------------------------------------------------------------------------- #
@router.callback_query(F.data == cb.CB_LOGIN_CREDENTIALS)
async def login_credentials_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.message.edit_text(
        "✉️ أدخل بريدك الإلكتروني أو رقم هاتفك المسجّل في TikTok:",
    )
    await state.set_state(LoginState.credentials_identifier)
    await query.answer()


@router.message(LoginState.credentials_identifier)
async def credentials_identifier(message: Message, state: FSMContext, user: User) -> None:
    identifier = validation.validate_login_identifier(message.text or "")
    if identifier is None:
        await message.answer("⚠️ القيمة غير صالحة. أرسل بريدًا إلكترونيًا أو رقم هاتف صحيح.")
        return
    temp_store.put(f"login_identifier:{user.telegram_id}", identifier, ttl=600)
    await message.answer("🔑 الآن أرسل كلمة المرور (لن تُحفظ ولن تظهر في السجلات):")
    await state.set_state(LoginState.credentials_password)


@router.message(LoginState.credentials_password)
async def credentials_password(message: Message, state: FSMContext, user: User) -> None:
    password = validation.validate_password(message.text or "")
    identifier = temp_store.get(f"login_identifier:{user.telegram_id}")
    if password is None or identifier is None:
        await message.answer("⚠️ حدث خطأ، أعد المحاولة من البداية.", reply_markup=back_to_menu())
        await state.clear()
        return

    client = await create_client()
    temp_store.put(_login_client_key(user.telegram_id), client, ttl=600)
    await client.set_credentials(identifier, password)

    try:
        result = await client.start_login("credentials")
    except TikTokError as exc:
        await _cleanup_pending(user.telegram_id, state)
        await message.answer(f"⚠️ {exc.user_message}", reply_markup=back_to_menu())
        return

    if isinstance(result, LoginChallenge) and result.kind == "otp":
        await message.answer("🔐 TikTok طلب رمز تحقق.\nأرسل رمز التحقق هنا:")
        await state.set_state(LoginState.otp)
        return

    # Direct success.
    await _complete_login(message.bot, message.chat.id, user.telegram_id, result)
    await state.clear()


@router.message(LoginState.otp)
async def otp_submit(message: Message, state: FSMContext, user: User) -> None:
    code = validation.validate_otp(message.text or "")
    if code is None:
        await message.answer("⚠️ رمز التحقق غير صالح. أرسل رمزًا مكوّنًا من أرقام.")
        return

    client = temp_store.get(_login_client_key(user.telegram_id))
    if client is None:
        await message.answer("⚠️ انتهت الجلسة، أعد المحاولة من البداية.", reply_markup=back_to_menu())
        await state.clear()
        return

    try:
        profile = await client.submit_otp(code)
    except TikTokOtpError:
        await message.answer("❌ رمز التحقق غير صحيح. أعد إرسال الرمز الصحيح.")
        return
    except TikTokError as exc:
        await _cleanup_pending(user.telegram_id, state)
        await message.answer(f"⚠️ {exc.user_message}", reply_markup=back_to_menu())
        return

    await _complete_login(message.bot, message.chat.id, user.telegram_id, profile)
    await state.clear()


# --------------------------------------------------------------------------- #
# Completion / cleanup
# --------------------------------------------------------------------------- #
async def _complete_login(bot, chat_id: int, user_id: int, profile) -> None:
    client = temp_store.pop(_login_client_key(user_id))
    temp_store.delete(f"login_identifier:{user_id}")

    account = await add_account(
        user_id,
        username=profile.username,
        tiktok_user_id=profile.user_id,
        display_name=profile.display_name,
    )
    await update_account_stats(account.id, profile.followers_count, profile.following_count)

    if client is not None:
        register(account.id, client)

    await bot.send_message(
        chat_id,
        f"✅ تم تسجيل الدخول بنجاح\n\nالحساب: @{profile.username}",
        reply_markup=account_actions(account.id),
    )


async def _cleanup_pending(user_id: int, state: FSMContext | None) -> None:
    task = temp_store.pop(_login_task_key(user_id))
    if task is not None and not task.done():
        task.cancel()
    client = temp_store.pop(_login_client_key(user_id))
    temp_store.delete(f"login_identifier:{user_id}")
    if client is not None:
        try:
            await client.close()
        except Exception:  # noqa: BLE001
            pass
    if state is not None:
        await state.clear()


async def cancel_login(message: Message) -> None:
    """Called from /cancel — aborts any in-flight login."""
    user = message.from_user
    if user is None:
        return
    await _cleanup_pending(user.id, None)
    await message.answer("تم إلغاء أي عملية تسجيل دخول جارية.", reply_markup=back_to_menu())
