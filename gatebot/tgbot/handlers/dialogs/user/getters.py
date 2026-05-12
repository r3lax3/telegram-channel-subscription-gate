import time

from aiogram.types import User

from aiogram_dialog import DialogManager
from dishka.integrations.aiogram_dialog import inject
from dishka import FromDishka

from core.config.settings import Settings
from core.interfaces.repositories.uow import UnitOfWork
from core.services.invite import InviteService
from core.services.payment import PaymentService


PAY_LINK_TTL_SECONDS = 30 * 60


@inject
async def main_menu_getter(settings: FromDishka[Settings], **kwargs):
    return {
        "support_link": settings.support_link,
    }


@inject
async def payment_menu_getter(
    event_from_user: User,
    dialog_manager: DialogManager,
    payment_service: FromDishka[PaymentService],
    **kwargs,
):
    now = time.time()
    cached_link = dialog_manager.dialog_data.get("pay_link")
    cached_at = dialog_manager.dialog_data.get("pay_link_at", 0)
    if cached_link and now - cached_at < PAY_LINK_TTL_SECONDS:
        return {"pay_link": cached_link}

    _, link = await payment_service.create_payment_link(
        telegram_id=event_from_user.id,
        username=event_from_user.username,
    )
    dialog_manager.dialog_data["pay_link"] = link
    dialog_manager.dialog_data["pay_link_at"] = now
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
        "subscription_end": end.strftime("%Y-%m-%d %H:%M UTC") if end else "—",
    }
