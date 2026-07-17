import logging
from datetime import datetime, timedelta

from aiogram import Bot

from core.config.settings import Settings
from core.interfaces.repositories.uow import UnitOfWork
from core.utils import utcnow
from infrastructure.astrobot.client import AstrobotClient
from infrastructure.database.models import User

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, uow: UnitOfWork, bot: Bot, settings: Settings) -> None:
        self.uow = uow
        self.bot = bot
        self.settings = settings

    async def activate_subscription(
        self, telegram_id: int, username: str | None, days: int
    ) -> User:
        user = await self.uow.users.get_or_create(telegram_id, username)
        now = utcnow()
        if user.subscription_end_date and user.subscription_end_date > now:
            user.subscription_end_date += timedelta(days=days)
        else:
            user.subscription_end_date = now + timedelta(days=days)
        user.is_active = True
        user.expiring_notice_sent = False
        await self.uow.users.update(user)
        await self.uow.commit()
        logger.info(
            "Subscription activated for user %s until %s",
            telegram_id, user.subscription_end_date,
        )
        await self._sync_to_astrobot(telegram_id, user.subscription_end_date)
        return user

    @staticmethod
    def has_active_subscription(user: User | None) -> bool:
        if user is None or not user.is_active or user.subscription_end_date is None:
            return False
        return user.subscription_end_date > utcnow()

    @staticmethod
    def is_legacy_client(user: User | None) -> bool:
        """«Старичок»: непрерывная подписка с даты отсечки (см. миграцию 0003).

        Доверяем флагу legacy_pricing: он сбрасывается при разрыве подписки
        (кик воркером, отзыв, прошедшая дата) и управляется из админки.
        """
        return user is not None and user.legacy_pricing

    async def kick_user(self, telegram_id: int) -> bool:
        try:
            await self.bot.ban_chat_member(self.settings.channel_id, telegram_id)
            await self.bot.unban_chat_member(
                self.settings.channel_id, telegram_id, only_if_banned=True
            )
            logger.info("User %s kicked from channel", telegram_id)
            return True
        except Exception:
            logger.exception("Failed to kick user %s from channel", telegram_id)
            return False

    async def get_expiring_users(self, days: int = 3) -> list[User]:
        return await self.uow.users.get_expiring_users(days)

    async def get_expired_users(self) -> list[User]:
        return await self.uow.users.get_expired_users()

    async def set_subscription_end(
        self, telegram_id: int, end_date: datetime
    ) -> User | None:
        user = await self.uow.users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        now = utcnow()
        user.subscription_end_date = end_date
        user.is_active = end_date > now
        if not user.is_active:
            user.legacy_pricing = False
            await self.kick_user(telegram_id)
        else:
            user.expiring_notice_sent = False
        await self.uow.users.update(user)
        await self.uow.commit()
        logger.info(
            "Subscription manually set for user %s until %s", telegram_id, end_date
        )
        if user.is_active:
            await self._sync_to_astrobot(telegram_id, end_date)
        return user

    async def set_legacy_pricing(
        self, telegram_id: int, enabled: bool
    ) -> User | None:
        user = await self.uow.users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        user.legacy_pricing = enabled
        await self.uow.users.update(user)
        await self.uow.commit()
        logger.info(
            "Legacy pricing %s for user %s",
            "enabled" if enabled else "disabled",
            telegram_id,
        )
        return user

    async def _sync_to_astrobot(
        self, telegram_id: int, subscription_end_date: datetime | None
    ) -> None:
        if not self.settings.astrobot_sync_enabled:
            return
        if subscription_end_date is None:
            return
        await AstrobotClient(self.settings).notify(
            telegram_id, subscription_end_date
        )

    async def revoke_subscription(self, telegram_id: int) -> User | None:
        user = await self.uow.users.get_by_telegram_id(telegram_id)
        if user is None:
            return None
        kicked = await self.kick_user(telegram_id)
        if not kicked:
            logger.warning(
                "Revoke for %s: kick failed; subscription state left untouched",
                telegram_id,
            )
            return None
        user.is_active = False
        user.subscription_end_date = None
        user.expiring_notice_sent = False
        user.legacy_pricing = False
        await self.uow.users.update(user)
        await self.uow.commit()
        logger.info("Subscription manually revoked for user %s", telegram_id)
        return user
