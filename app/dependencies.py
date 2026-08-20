"""Application container holding shared singletons.

Populated in main.py at startup; handlers and services read from here.
"""
from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage

from app.workers.operation_manager import OperationManager


@dataclass
class Container:
    bot: Bot
    operation_manager: OperationManager
    fsm_storage: MemoryStorage


_container: Container | None = None


def set_container(container: Container) -> None:
    global _container
    _container = container


def get_container() -> Container:
    if _container is None:
        raise RuntimeError("Container is not initialized yet")
    return _container
