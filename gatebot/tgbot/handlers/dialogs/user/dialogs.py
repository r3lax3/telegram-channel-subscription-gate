from aiogram.enums import ParseMode

from aiogram_dialog import Dialog, Window  # noqa: F401
from aiogram_dialog.widgets.kbd import Back, Column, Select, SwitchTo, Url
from aiogram_dialog.widgets.text import Const, Format

from tgbot.texts import (
    WELCOME,
    TARIFF_MENU,
    PAYMENT_INFO,
    SUBSCRIPTION_ACTIVE,
    BTN_BACK,
    BTN_PAY,
    BTN_RENEW,
    BTN_SUPPORT,
    BTN_PAY_LINK,
)
from tgbot.states import UserSG
from .getters import (
    main_menu_getter,
    tariff_menu_getter,
    payment_link_getter,
    subscription_active_getter,
)
from .handlers import on_tariff_selected


dialog = Dialog(
    Window(
        Format(WELCOME),
        SwitchTo(
            Const(BTN_PAY),
            id="pay",
            state=UserSG.payment_menu,
        ),
        Url(
            Const(BTN_SUPPORT),
            Format("{support_link}"),
        ),
        state=UserSG.main_menu,
        getter=main_menu_getter,
        parse_mode=ParseMode.HTML,
    ),
    Window(
        Format(TARIFF_MENU),
        Column(
            Select(
                Format("{item[label]}"),
                id="tariff",
                item_id_getter=lambda item: item["months"],
                items="tariffs",
                on_click=on_tariff_selected,
            ),
        ),
        Back(
            Const(BTN_BACK),
        ),
        getter=tariff_menu_getter,
        state=UserSG.payment_menu,
    ),
    Window(
        Const(PAYMENT_INFO),
        Url(
            Const(BTN_PAY_LINK),
            Format("{pay_link}"),
        ),
        SwitchTo(
            Const(BTN_BACK),
            id="back_to_tariffs",
            state=UserSG.payment_menu,
        ),
        getter=payment_link_getter,
        state=UserSG.payment_link,
    ),
    Window(
        Format(SUBSCRIPTION_ACTIVE),
        SwitchTo(
            Const(BTN_RENEW),
            id="renew",
            state=UserSG.payment_menu,
        ),
        Url(
            Const(BTN_SUPPORT),
            Format("{support_link}"),
        ),
        state=UserSG.subscription_active,
        getter=subscription_active_getter,
        parse_mode=ParseMode.HTML,
    ),
)
