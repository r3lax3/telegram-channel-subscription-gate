import logging

from aiogram import Router
from aiogram.types.error_event import ErrorEvent

logger = logging.getLogger(__name__)


def handle_error(error: ErrorEvent):
    logger.exception(
        "Unexpected exception %s while processing %s",
        error.exception.__class__.__name__,
        error.update.model_dump(exclude_none=True),
        exc_info=error.exception,
    )


def setup() -> Router:
    r = Router()
    r.errors.register(handle_error)

    return r

