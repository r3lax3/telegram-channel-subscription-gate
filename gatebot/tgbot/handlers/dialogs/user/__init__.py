from aiogram import Router

from tgbot.filters import IsSuperuser

from .dialogs import dialog


def setup() -> Router:
    r = Router()

    r.message.filter(IsSuperuser())
    r.callback_query.filter(IsSuperuser())

    r.include_router(dialog)

    return r
