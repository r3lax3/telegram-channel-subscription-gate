import asyncio
import logging

from aiohttp import web
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config.settings import Settings
from core.services.payment import PaymentService
from core.services.subscription import SubscriptionService
from infrastructure.database.uow import SQLUnitOfWork
from infrastructure.prodamus.client import ProdamusClient

logger = logging.getLogger(__name__)

SUCCESS_PAYMENT_STATUSES = ("success", "success_test_payment")


class WebhookServer:
    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
        bot: Bot,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.bot = bot
        self.app = web.Application()
        self.app.router.add_post("/prodamus/webhook", self.handle_prodamus_webhook)
        self.app.router.add_get("/health", self.handle_health)

    async def handle_health(self, request: web.Request) -> web.Response:
        return web.Response(text="OK")

    async def handle_prodamus_webhook(self, request: web.Request) -> web.Response:
        try:
            data = await request.post()
            data_dict = dict(data)
        except Exception:
            logger.exception("Failed to parse webhook data")
            return web.Response(status=400, text="Bad request")

        logger.info(
            "Webhook received: order_id=%s customer_extra=%s payment_status=%s",
            data_dict.get("order_id"),
            data_dict.get("customer_extra"),
            data_dict.get("payment_status"),
        )

        signature = data_dict.pop("sign", "") or request.headers.get("Sign", "")
        if not ProdamusClient.verify_signature(
            data_dict, str(signature), self.settings.prodamus_secret_key
        ):
            logger.warning("Webhook rejected: invalid signature (sign=%r)", signature)
            return web.Response(status=403, text="Invalid signature")

        customer_extra = data_dict.get("customer_extra")
        if not customer_extra or customer_extra == "0":
            logger.warning("Webhook rejected: missing customer_extra")
            return web.Response(status=400, text="Missing customer_extra")

        payment_status = data_dict.get("payment_status")
        if payment_status not in SUCCESS_PAYMENT_STATUSES:
            logger.info("Webhook ignored: payment_status=%s", payment_status)
            return web.Response(status=200, text="OK")

        async with self.session_factory() as session:
            uow = SQLUnitOfWork(session)
            payment_service = PaymentService(uow, self.settings)
            subscription_service = SubscriptionService(uow, self.bot, self.settings)

            payment = await payment_service.process_webhook(data_dict)
            if payment is None:
                logger.warning("Webhook: no matching payment processed")
                return web.Response(text="OK")

            logger.info(
                "Webhook: payment id=%s marked success for user_id=%s",
                payment.id, payment.user_id,
            )
            user = await uow.users.get_by_id(payment.user_id)
            if user is None:
                logger.error(
                    "Payment %s references missing user_id=%s",
                    payment.id, payment.user_id,
                )
                return web.Response(text="OK")

            try:
                logger.info(
                    "Activating subscription for telegram_id=%s", user.telegram_id
                )
                invite_link = await subscription_service.activate_subscription(
                    user.telegram_id, username=user.username
                )
                logger.info(
                    "Sending invite link to telegram_id=%s", user.telegram_id
                )
                await self.bot.send_message(
                    user.telegram_id,
                    f"Оплата прошла успешно!\n\nВаша ссылка для входа в канал: {invite_link}",
                )
                logger.info(
                    "Invite link delivered to telegram_id=%s", user.telegram_id
                )
            except Exception:
                logger.exception(
                    "Failed to activate subscription for %s", user.telegram_id
                )

        return web.Response(text="OK")

    async def start(self) -> None:
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.settings.webhook_port)
        await site.start()
        logger.info("Webhook server started on port %s", self.settings.webhook_port)
        try:
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()
