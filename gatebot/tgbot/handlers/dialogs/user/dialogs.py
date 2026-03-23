from aiogram import F
from aiogram.enums import ContentType

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Button, SwitchTo, Row, Url
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput

from tgbot.texts import (
    WELCOME,
    PAYMENT_INFO,
    BTN_BACK,
    BTN_ABOUT,
    BTN_PAY,
    BTN_QUESTION,
    BTN_PAY_LINK,
    BTN_OFFER
)
from tgbot.states import UserSG
from .handlers import offer_handler
from .getters import main_menu_getter, payment_menu_getter


dialog = Dialog(
    Window(
        Const(WELCOME),
        SwitchTo(
            Const(BTN_PAY),
            id="pay",
            state=UserSG.payment
        ),
        Url(
            Const(BTN_QUESTION),
            Format("{support_link}"),
        ),
        Url(
            Const(BTN_ABOUT),
            Format("{channel_description_link}"),
        ),
        state=UserSG.main_menu,
        getter=main_menu_getter
    ),
    Window(
        Const(PAYMENT_INFO),
        Url(
            Const(BTN_PAY_LINK),
            Format("{pay_link}")
        ),
        Button(
            Const(BTN_OFFER),
            id="offer",
            on_click=offer_handler
        ),
        Back(
            Const(BTN_BACK)
        ),
        getter=payment_menu_getter,
        state=UserSG.payment_menu
    )
)
