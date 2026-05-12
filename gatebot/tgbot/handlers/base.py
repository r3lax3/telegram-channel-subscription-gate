from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from aiogram_dialog import DialogManager, StartMode

from dishka import FromDishka
from dishka.integrations.aiogram import inject

from core.interfaces.repositories.uow import UnitOfWork
from core.services.subscription import SubscriptionService
from tgbot.filters import IsSuperuser
from tgbot.states import AdminSG, UserSG


def setup() -> Router:
    r = Router()

    @r.message(CommandStart())
    @inject
    async def cmd_start(
        message: Message,
        dialog_manager: DialogManager,
        uow: FromDishka[UnitOfWork],
    ):
        user = await uow.users.get_by_telegram_id(message.from_user.id)
        if SubscriptionService.has_active_subscription(user):
            target = UserSG.subscription_active
        else:
            target = UserSG.main_menu
        await dialog_manager.start(target, mode=StartMode.RESET_STACK)

    @r.message(Command("admin"), IsSuperuser())
    async def cmd_admin(message: Message, dialog_manager: DialogManager):
        await dialog_manager.start(AdminSG.adminpanel, mode=StartMode.RESET_STACK)

    return r
