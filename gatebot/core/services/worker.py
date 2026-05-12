import asyncio
import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config.settings import Settings
from core.services.subscription import SubscriptionService
from infrastructure.database.uow import SQLUnitOfWork
from tgbot.texts import SUBSCRIPTION_EXPIRING, SUBSCRIPTION_EXPIRED

logger = logging.getLogger(__name__)

WORKER_INTERVAL_SECONDS = 3600  # 1 hour
EXPIRING_NOTICE_DAYS = 3


async def subscription_worker(
    session_factory: async_sessionmaker[AsyncSession],
    bot: Bot,
    settings: Settings,
) -> None:
    logger.info("Subscription worker started")

    while True:
        try:
            async with session_factory() as session:
                uow = SQLUnitOfWork(session)
                service = SubscriptionService(uow, bot, settings)

                # 1. Notify users whose subscription expires in 3 days
                expiring = await service.get_expiring_users(days=EXPIRING_NOTICE_DAYS)
                for user in expiring:
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            SUBSCRIPTION_EXPIRING.format(days=EXPIRING_NOTICE_DAYS),
                        )
                    except Exception:
                        logger.exception(
                            "Failed to notify expiring user %s", user.telegram_id
                        )

                # 2. Kick expired users from channel
                expired = await service.get_expired_users()
                for user in expired:
                    try:
                        await service.kick_user(user.telegram_id)
                        user.is_active = False
                        await uow.users.update(user)
                        await bot.send_message(
                            user.telegram_id,
                            SUBSCRIPTION_EXPIRED,
                        )
                    except Exception:
                        logger.exception(
                            "Failed to process expired user %s", user.telegram_id
                        )

                await uow.commit()
                logger.info("Worker cycle: %d expiring, %d expired", len(expiring), len(expired))

        except Exception:
            logger.exception("Worker iteration failed")

        await asyncio.sleep(WORKER_INTERVAL_SECONDS)
