from aiogram.types import User

from dishka.integrations.aiogram_dialog import inject
from dishka import FromDishka

from core.config.settings import Settings
from core.interfaces.repositories.uow import UnitOfWork
from core.services.invite import InviteService
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


@inject
async def subscription_active_getter(
    event_from_user: User,
    settings: FromDishka[Settings],
    uow: FromDishka[UnitOfWork],
    invite_service: FromDishka[InviteService],
    **kwargs,
):
    user = await uow.users.get_by_telegram_id(event_from_user.id)
    invite_link = await invite_service.ensure_link()
    end = user.subscription_end_date if user else None
    return {
        "support_link": settings.support_link,
        "invite_link": invite_link,
        "subscription_end": end.strftime("%Y-%m-%d %H:%M") if end else "—",
    }
