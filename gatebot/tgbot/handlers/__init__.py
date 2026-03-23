from aiogram import Dispatcher
from aiogram_dialog.api.protocols import BgManagerFactory

from tgbot.handlers import base, errors, dialogs


async def setup_handlers(dp: Dispatcher) -> BgManagerFactory:
    dp.include_routers(
        errors.setup(),
        base.setup()
    )

    bg_manager_factory = dialogs.setup(dp)
    return bg_manager_factory
