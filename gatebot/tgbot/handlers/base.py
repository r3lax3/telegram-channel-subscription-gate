from aiogram import Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_dialog import DialogManager, StartMode

from tgbot.states import UserSG


def setup() -> Router:
    r = Router()

    @r.message(CommandStart())
    async def cmd_start(message: Message, dialog_manager: DialogManager):
        await dialog_manager.start(UserSG.main_menu, mode=StartMode.RESET_STACK)

    return r
