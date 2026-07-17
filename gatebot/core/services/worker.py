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
PENDING_PAYMENT_TTL_HOURS = 48


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

                expiring = await uow.users.get_expiring_unnotified(EXPIRING_NOTICE_DAYS)
                notified = 0
                for user in expiring:
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            SUBSCRIPTION_EXPIRING.format(days=EXPIRING_NOTICE_DAYS),
                        )
                        user.expiring_notice_sent = True
                        await uow.users.update(user)
                        notified += 1
                    except Exception:
                        logger.exception(
                            "Failed to notify expiring user %s", user.telegram_id
                        )

                expired = await service.get_expired_users()
                kicked = 0
                for user in expired:
                    if not await service.kick_user(user.telegram_id):
                        continue
                    user.is_active = False
                    user.expiring_notice_sent = False
                    user.legacy_pricing = False
                    await uow.users.update(user)
                    try:
                        await bot.send_message(
                            user.telegram_id, SUBSCRIPTION_EXPIRED
                        )
                    except Exception:
                        logger.exception(
                            "Failed to send expiry message to %s", user.telegram_id
                        )
                    kicked += 1

                stale = await uow.payments.expire_stale_pending(PENDING_PAYMENT_TTL_HOURS)

                await uow.commit()
                logger.info(
                    "Worker cycle: notified=%d, kicked=%d, expired_payments=%d",
                    notified, kicked, stale,
                )

        except Exception:
            logger.exception("Worker iteration failed")

        await asyncio.sleep(WORKER_INTERVAL_SECONDS)
