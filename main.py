"""
Main entry point.

Starts the bot (polling) + aiohttp server (for Prodamus webhooks) + scheduler.
"""

import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, WEBHOOK_HOST, WEBHOOK_PORT
from database import init_db
from handlers import router
from webhook_handler import setup_webhook_routes
from scheduler import run_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set!")
        return

    # Init DB
    await init_db()
    logger.info("Database initialized")

    # Init bot and dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    # Setup aiohttp app for Prodamus webhooks
    app = web.Application()
    app["bot"] = bot
    setup_webhook_routes(app)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBHOOK_HOST, WEBHOOK_PORT)
    await site.start()
    logger.info(f"Webhook server started on {WEBHOOK_HOST}:{WEBHOOK_PORT}")

    # Start scheduler in background
    scheduler_task = asyncio.create_task(run_scheduler(bot))

    # Start polling
    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler_task.cancel()
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
