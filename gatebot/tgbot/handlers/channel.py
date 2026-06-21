import logging

from aiogram import Bot, Router
from aiogram.types import ChatJoinRequest

from dishka import FromDishka
from dishka.integrations.aiogram import inject

from core.config.settings import Settings
from core.interfaces.repositories.uow import UnitOfWork
from core.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)


def setup() -> Router:
    r = Router()

    @r.chat_join_request()
    @inject
    async def on_join_request(
        event: ChatJoinRequest,
        bot: FromDishka[Bot],
        settings: FromDishka[Settings],
        uow: FromDishka[UnitOfWork],
    ):
        allowed_chats = {settings.channel_id}
        if settings.linked_chat_id:
            allowed_chats.add(settings.linked_chat_id)

        if event.chat.id not in allowed_chats:
            logger.info(
                "Ignored join request from unrelated chat %s", event.chat.id
            )
            return

        user = await uow.users.get_by_telegram_id(event.from_user.id)
        if user is not None and event.from_user.username and user.username != event.from_user.username:
            user.username = event.from_user.username
            await uow.users.update(user)
            await uow.commit()

        if SubscriptionService.has_active_subscription(user):
            try:
                await event.approve()
                logger.info(
                    "Approved join request for user %s in chat %s",
                    event.from_user.id, event.chat.id,
                )
            except Exception:
                logger.exception(
                    "Failed to approve join for %s", event.from_user.id
                )
            return

        try:
            await event.decline()
            logger.info(
                "Declined join request for user %s in chat %s",
                event.from_user.id, event.chat.id,
            )
        except Exception:
            logger.exception("Failed to decline join for %s", event.from_user.id)

        for chat_id in allowed_chats:
            try:
                await bot.ban_chat_member(chat_id, event.from_user.id)
                await bot.unban_chat_member(
                    chat_id, event.from_user.id, only_if_banned=True
                )
            except Exception:
                logger.exception(
                    "Failed safety kick for %s from chat %s after declined join",
                    event.from_user.id, chat_id,
                )

    return r
