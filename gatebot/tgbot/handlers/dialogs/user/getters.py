import time

from aiogram.types import User

from aiogram_dialog import DialogManager
from dishka.integrations.aiogram_dialog import inject
from dishka import FromDishka

from core.config.settings import Settings
from core.interfaces.repositories.uow import UnitOfWork
from core.services.invite import InviteService
from core.services.payment import PaymentService
from core.services.pricing import TARIFFS, get_tariff, monthly_price, tariff_price
from core.services.subscription import SubscriptionService
from tgbot.texts import BTN_TARIFF, BTN_TARIFF_DISCOUNT, PRODAMUS_PRODUCT_NAME


PAY_LINK_TTL_SECONDS = 30 * 60


async def _monthly_price_for(
    telegram_id: int, uow: UnitOfWork, settings: Settings
) -> int:
    user = await uow.users.get_by_telegram_id(telegram_id)
    legacy = SubscriptionService.is_legacy_client(user)
    return monthly_price(settings, legacy)


@inject
async def main_menu_getter(
    event_from_user: User,
    settings: FromDishka[Settings],
    uow: FromDishka[UnitOfWork],
    **kwargs,
):
    base = await _monthly_price_for(event_from_user.id, uow, settings)
    return {
        "support_link": settings.support_link,
        "first_name": event_from_user.first_name,
        "price_month": base,
    }


@inject
async def tariff_menu_getter(
    event_from_user: User,
    settings: FromDishka[Settings],
    uow: FromDishka[UnitOfWork],
    **kwargs,
):
    base = await _monthly_price_for(event_from_user.id, uow, settings)
    prices = {tariff.months: tariff_price(base, tariff) for tariff in TARIFFS}
    tariffs = []
    for tariff in TARIFFS:
        template = BTN_TARIFF_DISCOUNT if tariff.discount_percent else BTN_TARIFF
        tariffs.append(
            {
                "months": tariff.months,
                "label": template.format(
                    title=tariff.title,
                    price=prices[tariff.months],
                    discount=tariff.discount_percent,
                ),
            }
        )
    return {
        "tariffs": tariffs,
        "price_month": prices[1],
        "price_quarter": prices[3],
        "price_half_year": prices[6],
    }


@inject
async def payment_link_getter(
    event_from_user: User,
    dialog_manager: DialogManager,
    settings: FromDishka[Settings],
    uow: FromDishka[UnitOfWork],
    payment_service: FromDishka[PaymentService],
    **kwargs,
):
    months = int(dialog_manager.dialog_data.get("tariff_months", 1))
    tariff = get_tariff(months) or TARIFFS[0]
    base = await _monthly_price_for(event_from_user.id, uow, settings)
    price = tariff_price(base, tariff)

    now = time.time()
    cache_key = f"{tariff.months}:{price}"
    cached_link = dialog_manager.dialog_data.get("pay_link")
    cached_key = dialog_manager.dialog_data.get("pay_link_key")
    cached_at = dialog_manager.dialog_data.get("pay_link_at", 0)
    if cached_link and cached_key == cache_key and now - cached_at < PAY_LINK_TTL_SECONDS:
        return {"pay_link": cached_link}

    _, link = await payment_service.create_payment_link(
        telegram_id=event_from_user.id,
        username=event_from_user.username,
        amount=price,
        days=tariff.days,
        product_name=PRODAMUS_PRODUCT_NAME.format(title=tariff.title.lower()),
    )
    dialog_manager.dialog_data["pay_link"] = link
    dialog_manager.dialog_data["pay_link_key"] = cache_key
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
