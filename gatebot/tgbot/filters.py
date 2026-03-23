# tgbot/filters/superuser.py
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from dishka import FromDishka
from dishka.integrations.aiogram import inject

from config.settings import Settings


class IsSuperuser(BaseFilter):
    @inject
    async def __call__(
        self,
        event: Message | CallbackQuery,
        settings: FromDishka[Settings],
    ) -> bool:
        return event.from_user.id == settings.owner_id
