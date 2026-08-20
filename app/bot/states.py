"""FSM states for multi-step flows."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class LoginState(StatesGroup):
    credentials_identifier = State()
    credentials_password = State()
    otp = State()


class BroadcastState(StatesGroup):
    waiting_text = State()
