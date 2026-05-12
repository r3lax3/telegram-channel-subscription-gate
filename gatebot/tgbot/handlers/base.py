from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram_dialog import DialogManager, StartMode

from tgbot.filters import IsSuperuser
from tgbot.states import AdminSG, UserSG


def setup() -> Router:
    r = Router()

    @r.message(CommandStart())
    async def cmd_start(message: Message, dialog_manager: DialogManager):
        await dialog_manager.start(UserSG.main_menu, mode=StartMode.RESET_STACK)

    @r.message(Command("admin"), IsSuperuser())
    async def cmd_admin(message: Message, dialog_manager: DialogManager):
        await dialog_manager.start(AdminSG.adminpanel, mode=StartMode.RESET_STACK)

    return r
