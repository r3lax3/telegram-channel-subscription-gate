from aiogram.enums import ParseMode

from aiogram_dialog import Dialog, Window  # noqa: F401
from aiogram_dialog.widgets.kbd import Back, SwitchTo, Url
from aiogram_dialog.widgets.text import Const, Format

from tgbot.texts import (
    WELCOME,
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
    payment_menu_getter,
    subscription_active_getter,
)


dialog = Dialog(
    Window(
        Const(WELCOME),
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
    ),
    Window(
        Const(PAYMENT_INFO),
        Url(
            Const(BTN_PAY_LINK),
            Format("{pay_link}"),
        ),
        Back(
            Const(BTN_BACK),
        ),
        getter=payment_menu_getter,
        state=UserSG.payment_menu,
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
