from aiogram import Bot, Dispatcher

from core.di import DependencyInjector
from core.dialogs import user_dialog, admin_dialog


async def on_startup(di: DependencyInjector):
    bot = Bot(di.settings.bot_token)
    dp = Dispatcher(di=di)

    dp.include_routers(user_dialog, admin_dialog)

    await dp.start_polling(bot)



async def on_shutdown(di: DependencyInjector):
    ...

