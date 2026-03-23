from aiogram import Dispatcher, Router, F
from aiogram.enums import ChatType

from aiogram_dialog import setup_dialogs
from aiogram_dialog.api.protocols import BgManagerFactory
from aiogram_dialog.manager.message_manager import MessageManager

from . import superuser, user


def setup(dp: Dispatcher) -> BgManagerFactory:
    dialogs_router = Router()
    dialogs_router.message.filter(F.chat.type == ChatType.PRIVATE)

    dialogs_router.include_router(superuser.setup())
    dialogs_router.include_router(user.setup())

    bg_manager_factory = setup_dialogs(dialogs_router, message_manager=MessageManager())

    dp.include_router(dialogs_router)

    return bg_manager_factory
