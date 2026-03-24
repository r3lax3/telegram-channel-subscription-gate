from aiogram.types import User

from dishka.integrations.aiogram_dialog import inject
from dishka import FromDishka

from core.config.settings import Settings
from core.services.payment import PaymentService


@inject
async def main_menu_getter(settings: FromDishka[Settings], **kwargs):
    return {
        "support_link": settings.support_link,
    }


@inject
async def payment_menu_getter(
    event_from_user: User,
    payment_service: FromDishka[PaymentService],
    **kwargs,
):
    link = await payment_service.create_payment_link(
        telegram_id=event_from_user.id,
        username=event_from_user.username,
    )
    return {"pay_link": link}
