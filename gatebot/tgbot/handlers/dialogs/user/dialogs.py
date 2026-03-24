from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, SwitchTo, Url
from aiogram_dialog.widgets.text import Const, Format

from tgbot.texts import (
    WELCOME,
    PAYMENT_INFO,
    BTN_BACK,
    BTN_PAY,
    BTN_SUPPORT,
    BTN_PAY_LINK,
)
from tgbot.states import UserSG
from .getters import main_menu_getter, payment_menu_getter


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
)
