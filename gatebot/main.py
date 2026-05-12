import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram_dialog import BgManagerFactory
from dishka import make_async_container
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config.settings import Settings
from core.runner import AppRunner
from core.services.invite import InviteService
from core.services.worker import subscription_worker
from core.utils import setup_logging_settings
from infrastructure.webhook.server import WebhookServer
from main_factory import get_all_dishka_providers


setup_logging_settings()
logger = logging.getLogger(__name__)


async def main():
    runner = AppRunner()

    dishka = make_async_container(*get_all_dishka_providers())

    dp = await dishka.get(Dispatcher)
    bot = await dishka.get(Bot)
    settings = await dishka.get(Settings)
    session_factory = await dishka.get(async_sessionmaker[AsyncSession])
    bg_manager_factory = await dishka.get(BgManagerFactory)
    invite_service = await dishka.get(InviteService)

    await bot.delete_webhook(drop_pending_updates=True)

    invite_link = await invite_service.ensure_link()
    logger.info("Channel invite link ready: %s", invite_link)

    webhook_server = WebhookServer(
        settings=settings,
        session_factory=session_factory,
        bot=bot,
        bg_manager_factory=bg_manager_factory,
    )

    await runner.run(
        dp.start_polling(bot),
        subscription_worker(session_factory, bot, settings),
        webhook_server.start(),
    )


if __name__ == "__main__":
    asyncio.run(main())
