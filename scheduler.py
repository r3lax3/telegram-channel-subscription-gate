"""
Subscription checker — runs periodically to:
1. Attempt recurring payments for expiring subscriptions
2. Notify users about expiring subscriptions
3. Kick users with expired subscriptions
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot

from config import RECURRING_DAYS_BEFORE, SUBSCRIPTION_DAYS
from database import (
    get_expiring_subscriptions,
    get_expired_subscriptions,
    deactivate_subscription,
    create_subscription,
    create_payment,
    update_payment_status,
)
from channel_service import kick_user_from_channel
from prodamus import generate_order_id, charge_recurring
import texts

logger = logging.getLogger(__name__)

# Track which subscriptions we already tried to renew (to avoid spamming)
_notified: set[int] = set()
_renewal_attempted: set[int] = set()


async def check_expiring_subscriptions(bot: Bot):
    """
    For subscriptions expiring within RECURRING_DAYS_BEFORE days:
    1. Try recurring payment if token exists
    2. Notify user if recurring failed or no token
    """
    subs = await get_expiring_subscriptions(RECURRING_DAYS_BEFORE)

    for sub in subs:
        sub_id = sub["id"]
        user_id = sub["user_id"]
        recurring_token = sub.get("recurring_token")

        # Try recurring payment (once per subscription)
        if sub_id not in _renewal_attempted and recurring_token:
            _renewal_attempted.add(sub_id)
            try:
                order_id = generate_order_id(user_id)
                result = await charge_recurring(recurring_token, order_id)

                if result.get("http_status") == 200 and result.get("status") == "success":
                    # Recurring payment succeeded — extend subscription
                    now = datetime.now(timezone.utc)
                    expires_at = datetime.fromisoformat(sub["expires_at"])
                    new_expires = expires_at + timedelta(days=SUBSCRIPTION_DAYS)

                    await create_subscription(
                        user_id=user_id,
                        starts_at=expires_at.isoformat(),
                        expires_at=new_expires.isoformat(),
                        recurring_token=recurring_token,
                    )
                    await deactivate_subscription(sub_id)

                    logger.info(f"Recurring payment succeeded for user {user_id}, sub extended to {new_expires}")
                    continue
                else:
                    logger.warning(f"Recurring payment failed for user {user_id}: {result}")
            except Exception as e:
                logger.error(f"Recurring payment error for user {user_id}: {e}")

        # Notify user about expiring subscription (once)
        if sub_id not in _notified:
            _notified.add(sub_id)
            expires_at = datetime.fromisoformat(sub["expires_at"])
            days_left = max(1, (expires_at - datetime.now(timezone.utc)).days)

            try:
                if recurring_token:
                    msg = texts.RECURRING_PAYMENT_FAILED
                else:
                    msg = texts.SUBSCRIPTION_EXPIRING.format(days=days_left)
                await bot.send_message(user_id, msg, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")


async def check_expired_subscriptions(bot: Bot):
    """Deactivate expired subscriptions and kick users from channel."""
    expired = await get_expired_subscriptions()

    for sub in expired:
        user_id = sub["user_id"]
        sub_id = sub["id"]

        await deactivate_subscription(sub_id)
        await kick_user_from_channel(bot, user_id)

        try:
            await bot.send_message(user_id, texts.SUBSCRIPTION_EXPIRED, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send expiry message to user {user_id}: {e}")

        logger.info(f"Subscription {sub_id} expired, user {user_id} kicked")

    # Clean up tracking sets for deactivated subs
    expired_ids = {sub["id"] for sub in expired}
    _notified.difference_update(expired_ids)
    _renewal_attempted.difference_update(expired_ids)


async def run_scheduler(bot: Bot, interval_seconds: int = 3600):
    """
    Periodically check subscriptions.

    Default interval: 1 hour.
    """
    logger.info(f"Scheduler started, interval={interval_seconds}s")
    while True:
        try:
            await check_expiring_subscriptions(bot)
            await check_expired_subscriptions(bot)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        await asyncio.sleep(interval_seconds)
