from aiogram import Router

from .dialogs import dialog


def setup() -> Router:
    r = Router()
    r.include_router(dialog)
    return r
