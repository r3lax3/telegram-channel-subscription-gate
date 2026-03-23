"""
Prodamus webhook handler.

Receives payment notifications from Prodamus and:
1. Verifies signature
2. Updates payment status
3. Creates/extends subscription
4. Sends invite link to user
"""

import logging
from datetime import datetime, timedelta, timezone

from aiohttp import web
from aiogram import Bot

from config import SUBSCRIPTION_DAYS, WEBHOOK_PATH
from database import (
    get_payment_by_order_id,
    update_payment_status,
    create_subscription,
    get_active_subscription,
    update_subscription_recurring_token,
)
from channel_service import get_or_create_invite_link
from prodamus import verify_webhook_signature
import texts

logger = logging.getLogger(__name__)


async def handle_prodamus_webhook(request: web.Request) -> web.Response:
    """Process Prodamus payment webhook."""
    bot: Bot = request.app["bot"]

    try:
        data = await request.json()
    except Exception:
        try:
            data = dict(await request.post())
        except Exception:
            logger.error("Failed to parse webhook body")
            return web.Response(status=400, text="Bad request")

    # Verify signature
    signature = request.headers.get("Sign", "") or data.get("sign", "")
    if not verify_webhook_signature(data, signature):
        logger.warning("Invalid webhook signature")
        return web.Response(status=403, text="Invalid signature")

    order_id = data.get("order_id") or data.get("order_num", "")
    payment_status = data.get("payment_status", "").lower()
    prodamus_payment_id = str(data.get("payment_id", ""))
    recurring_token = data.get("subscription_token") or data.get("recurring_token", "")
    customer_extra = data.get("customer_extra", "")  # user_id we passed

    logger.info(f"Webhook: order={order_id}, status={payment_status}, user={customer_extra}")

    if not order_id:
        return web.Response(status=400, text="Missing order_id")

    # Check payment exists
    payment = await get_payment_by_order_id(order_id)
    if not payment:
        logger.warning(f"Payment not found for order {order_id}")
        return web.Response(status=404, text="Payment not found")

    user_id = payment["user_id"]

    if payment_status == "success":
        # Update payment
        await update_payment_status(
            order_id=order_id,
            status="success",
            prodamus_payment_id=prodamus_payment_id,
            recurring_token=recurring_token,
        )

        # Create subscription
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=SUBSCRIPTION_DAYS)

        sub_id = await create_subscription(
            user_id=user_id,
            starts_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            recurring_token=recurring_token or None,
        )

        # Get invite link and notify user
        try:
            invite_link = await get_or_create_invite_link(bot)
            await bot.send_message(
                user_id,
                texts.PAYMENT_SUCCESS.format(invite_link=invite_link),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Failed to send success message to user {user_id}: {e}")

        logger.info(f"Subscription created for user {user_id}, expires {expires_at}")

    elif payment_status in ("fail", "failed", "error"):
        await update_payment_status(order_id=order_id, status="failed")

        try:
            await bot.send_message(user_id, texts.PAYMENT_FAILED, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send failure message to user {user_id}: {e}")

    else:
        # Other statuses (pending, etc.) — just update
        await update_payment_status(order_id=order_id, status=payment_status)

    return web.Response(status=200, text="OK")


def setup_webhook_routes(app: web.Application):
    """Register webhook routes."""
    app.router.add_post(WEBHOOK_PATH, handle_prodamus_webhook)
