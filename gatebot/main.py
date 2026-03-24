import asyncio
import logging

from aiogram import Dispatcher, Bot
from dishka import make_async_container
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config.settings import Settings
from core.runner import AppRunner
from core.services.worker import subscription_worker
from infrastructure.webhook.server import WebhookServer
from main_factory import get_all_dishka_providers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    runner = AppRunner()

    dishka = make_async_container(*get_all_dishka_providers())

    dp = await dishka.get(Dispatcher)
    bot = await dishka.get(Bot)
    settings = await dishka.get(Settings)
    session_factory = await dishka.get(async_sessionmaker[AsyncSession])

    await bot.delete_webhook(drop_pending_updates=True)

    webhook_server = WebhookServer(
        settings=settings,
        session_factory=session_factory,
        bot=bot,
    )

    await runner.run(
        dp.start_polling(bot),
        subscription_worker(session_factory, bot, settings),
        webhook_server.start(),
    )


if __name__ == "__main__":
    asyncio.run(main())
