import asyncio
import logging

from aiohttp import web
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config.settings import Settings
from core.services.payment import PaymentService
from core.services.subscription import SubscriptionService
from infrastructure.database.uow import SQLUnitOfWork
from infrastructure.prodamus.client import _create_hmac
from infrastructure.prodamus.client import ProdamusClient

logger = logging.getLogger(__name__)


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

        # signature = data_dict.pop("sign", "") or request.headers.get("Sign", "")
        # if not ProdamusClient.verify_signature(
        #     data_dict, str(signature), self.settings.prodamus_secret_key
        # ):
        #     local_signature = _create_hmac(data_dict, self.settings.prodamus_secret_key)
        #     logger.warning(f"Invalid webhook signature (local: \"{local_signature}\", external: \"{signature}\")")
        #     logger.warning(f"{data}")
        #     return web.Response(status=403, text="Invalid signature")
        #
        payment_status = data_dict.get("payment_status")
        if payment_status != "success":
            logger.info("Webhook ignored: payment_status=%s", payment_status)
            return web.Response(status=200, text="OK")

        async with self.session_factory() as session:
            uow = SQLUnitOfWork(session)
            payment_service = PaymentService(uow, self.settings)
            subscription_service = SubscriptionService(uow, self.bot, self.settings)

            processed = await payment_service.process_webhook(data_dict)
            if processed:
                try:
                    order_id = int(data_dict.get('order_id'))
                    payment = await uow.payments.get_by_order_id(order_id)
                    telegram_id = payment.user_id

                    invite_link = await subscription_service.activate_subscription(
                        telegram_id, username=None
                    )
                    await self.bot.send_message(
                        telegram_id,
                        f"Оплата прошла успешно!\n\nВаша ссылка для входа в канал: {invite_link}",
                    )
                except Exception:
                    logger.exception(
                        "Failed to activate subscription for %s", telegram_id
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
