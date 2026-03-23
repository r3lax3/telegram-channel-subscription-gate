from dishka.integrations.aiogram_dialog import inject
from dishka import FromDishka

from config.settings import Settings


@inject
async def main_menu_getter(settings: FromDishka[Settings], **kwargs):
    return {
        "support_link": settings.support_link,
        "channel_description_link": settings.channel_description_link
    }


async def payment_menu_getter():
    ...
