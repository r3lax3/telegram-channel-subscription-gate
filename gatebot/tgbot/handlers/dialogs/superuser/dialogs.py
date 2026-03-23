from aiogram import F
from aiogram.enums import ContentType

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Button, SwitchTo, Row
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.input import MessageInput

from tgbot.states import AdminSG

from .handlers import (
    approve_broadcast,
    clear_broadcast_content,
    broadcast_content_handler
)


dialog = Dialog(
    Window(
        Const("Adminpanel – Choose action below"),
        SwitchTo(
            Const("Broadcast"),
            id="broadcast",
            state=AdminSG.broadcast_menu
        ),
        SwitchTo(
            Const("Statistic"),
            id="statistic",
            state=AdminSG.statistic
        ),
        state=AdminSG.adminpanel
    ),

    Window(
        Const(
            "Push \"Approve\" button to send broadcast or update broadcast content",
            when=F["have_broadcast_content"]
        ),
        # or
        Const(
            "Send message to set broadcast content",
            when=~F["have_broadcast_content"]
        ),

        MessageInput(
            func=broadcast_content_handler,
            content_types=[ContentType.TEXT, ContentType.PHOTO],
        ),
        Row(
            Button(
                Const("Approve"),
                id="approve_broadcast",
                on_click=approve_broadcast,
            ),
            Button(
                Const("Clear"),
                id="clear_broadcast_content",
                on_click=clear_broadcast_content,
            ),
            when=F["have_broadcast_content"]
        ),
        Back(Const("Back")),
        state=AdminSG.broadcast_menu,
    )
)
