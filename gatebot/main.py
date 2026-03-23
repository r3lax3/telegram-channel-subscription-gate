import asyncio

from aiogram import Dispatcher, Bot
from dishka import make_async_container

from core.runner import AppRunner
from main_factory import get_all_dishka_providers


async def main():
    runner = AppRunner()

    dishka = make_async_container(*get_all_dishka_providers())

    dp = await dishka.get(Dispatcher)

    bot = await dishka.get(Bot)
    await bot.delete_webhook(drop_pending_updates=True)

    await runner.run(
        dp.start_polling(bot),  # 1. Telegram bot
        ...,  # 2. Worker that delete users from channel and trying to renew the susbscription
        ...,  # 3. Payment webhook handler
    )


if __name__ == "__main__":
    asyncio.run(main())

