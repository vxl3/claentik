"""Entry-point commands and the main menu."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot import callbacks as cb
from app.keyboards.main import back_to_menu, main_menu
from app.models.user import User
from app.security.access import is_owner
from app.utils.text import HELP_TEXT, MAIN_MENU

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, user: User) -> None:
    first = user.first_name or "صديقي"
    owner = is_owner(user)
    text = (
        f"👋 أهلاً بك يا {first} في بوت إدارة TikTok\n\n"
        "أضف حساب TikTok الخاص بك وابدأ بتنظيف متابعيك ومتابَعيك بسهولة."
    )
    await message.answer(text, reply_markup=main_menu(is_owner=owner))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=back_to_menu())


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    from app.handlers.settings import show_settings

    await show_settings(message)


@router.message(Command("accounts"))
async def cmd_accounts(message: Message, user: User) -> None:
    from app.handlers.accounts import show_accounts

    await show_accounts(message, user)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    from app.handlers.login import cancel_login

    await cancel_login(message)


@router.callback_query(F.data == cb.CB_BACK_TO_MENU)
async def back_to_main_menu(query: CallbackQuery, user: User) -> None:
    owner = is_owner(user)
    await query.message.edit_text(MAIN_MENU, reply_markup=main_menu(is_owner=owner))
    await query.answer()
