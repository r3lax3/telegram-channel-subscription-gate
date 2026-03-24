import logging
from datetime import datetime, timedelta

from aiogram import Bot

from core.config.settings import Settings
from core.interfaces.repositories.uow import UnitOfWork
from infrastructure.database.models import User

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, uow: UnitOfWork, bot: Bot, settings: Settings) -> None:
        self.uow = uow
        self.bot = bot
        self.settings = settings

    async def activate_subscription(
        self, telegram_id: int, username: str | None
    ) -> str:
        user = await self.uow.users.get_or_create(telegram_id, username)
        now = datetime.utcnow()
        if user.subscription_end_date and user.subscription_end_date > now:
            user.subscription_end_date += timedelta(days=self.settings.subscription_days)
        else:
            user.subscription_end_date = now + timedelta(days=self.settings.subscription_days)
        user.is_active = True
        await self.uow.users.update(user)
        await self.uow.commit()

        invite_link = await self.bot.create_chat_invite_link(
            chat_id=self.settings.channel_id,
            member_limit=1,
        )
        return invite_link.invite_link

    async def kick_user(self, telegram_id: int) -> None:
        try:
            await self.bot.ban_chat_member(self.settings.channel_id, telegram_id)
            await self.bot.unban_chat_member(
                self.settings.channel_id, telegram_id, only_if_banned=True
            )
        except Exception:
            logger.exception("Failed to kick user %s from channel", telegram_id)

    async def get_expiring_users(self, days: int = 3) -> list[User]:
        return await self.uow.users.get_expiring_users(days)

    async def get_expired_users(self) -> list[User]:
        return await self.uow.users.get_expired_users()
