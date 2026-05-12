from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from core.interfaces.repositories.uow import UnitOfWork
from core.services.stats import StatsService
from tgbot.texts import ADMIN_STATS, ADMIN_USER_CARD, ADMIN_USER_NOT_FOUND


def _fmt_dt(value) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M")


@inject
async def user_card_getter(
    dialog_manager,
    uow: FromDishka[UnitOfWork],
    **kwargs,
):
    telegram_id = dialog_manager.dialog_data.get("selected_telegram_id")
    if not telegram_id:
        return {"card": ADMIN_USER_NOT_FOUND, "has_user": False}

    user = await uow.users.get_by_telegram_id(int(telegram_id))
    if user is None:
        return {"card": ADMIN_USER_NOT_FOUND, "has_user": False}

    card = ADMIN_USER_CARD.format(
        id=user.id,
        telegram_id=user.telegram_id,
        username=f"@{user.username}" if user.username else "—",
        is_active="да" if user.is_active else "нет",
        subscription_end_date=_fmt_dt(user.subscription_end_date),
        created_at=_fmt_dt(user.created_at),
    )
    return {"card": card, "has_user": True}


@inject
async def stats_getter(
    dialog_manager,
    stats_service: FromDishka[StatsService],
    **kwargs,
):
    snap = await stats_service.collect()
    return {
        "stats": ADMIN_STATS.format(
            total_users=snap.total_users,
            active_subscribers=snap.active_subscribers,
            inactive_users=snap.inactive_users,
            expiring_soon=snap.expiring_soon,
            paid_count=snap.paid_count,
            pending_count=snap.pending_count,
            total_revenue=snap.total_revenue,
            revenue_30d=snap.revenue_30d,
        )
    }
