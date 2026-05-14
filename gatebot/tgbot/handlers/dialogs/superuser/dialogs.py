from aiogram import F
from aiogram.enums import ContentType

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Back, Button, SwitchTo, Row
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.input import MessageInput

from tgbot.states import AdminSG
from tgbot.texts import (
    ADMIN_BROADCAST_PROMPT,
    ADMIN_BROADCAST_READY,
    ADMIN_EXTEND_PROMPT,
    ADMIN_MAIN,
    ADMIN_USER_PROMPT,
    BTN_ADMIN_BROADCAST,
    BTN_ADMIN_CLEAR,
    BTN_ADMIN_EXTEND,
    BTN_ADMIN_FIND_ANOTHER,
    BTN_ADMIN_REVOKE,
    BTN_ADMIN_SEND,
    BTN_ADMIN_STATS,
    BTN_ADMIN_USERS,
    BTN_BACK,
)

from .getters import stats_getter, user_card_getter
from .handlers import (
    approve_broadcast,
    broadcast_content_handler,
    clear_broadcast_content,
    extend_date_handler,
    revoke_user_subscription,
    user_search_handler,
)


dialog = Dialog(
    Window(
        Const(ADMIN_MAIN),
        SwitchTo(
            Const(BTN_ADMIN_BROADCAST),
            id="broadcast",
            state=AdminSG.broadcast_menu,
        ),
        SwitchTo(
            Const(BTN_ADMIN_USERS),
            id="users",
            state=AdminSG.users_search,
        ),
        SwitchTo(
            Const(BTN_ADMIN_STATS),
            id="statistic",
            state=AdminSG.statistic,
        ),
        state=AdminSG.adminpanel,
    ),

    # ---- Broadcast ----
    Window(
        Const(ADMIN_BROADCAST_READY, when=F["have_broadcast_content"]),
        Const(ADMIN_BROADCAST_PROMPT, when=~F["have_broadcast_content"]),
        MessageInput(
            func=broadcast_content_handler,
            content_types=[ContentType.TEXT, ContentType.PHOTO],
        ),
        Row(
            Button(
                Const(BTN_ADMIN_SEND),
                id="approve_broadcast",
                on_click=approve_broadcast,
                when=F["have_broadcast_content"],
            ),
            Button(
                Const(BTN_ADMIN_CLEAR),
                id="clear_broadcast_content",
                on_click=clear_broadcast_content,
                when=F["have_broadcast_content"],
            ),
        ),
        Back(Const(BTN_BACK)),
        state=AdminSG.broadcast_menu,
    ),

    # ---- Users: search ----
    Window(
        Const(ADMIN_USER_PROMPT),
        MessageInput(
            func=user_search_handler,
            content_types=[ContentType.TEXT],
        ),
        SwitchTo(
            Const(BTN_BACK),
            id="users_search_back",
            state=AdminSG.adminpanel,
        ),
        state=AdminSG.users_search,
    ),

    # ---- Users: card ----
    Window(
        Format("{card}"),
        SwitchTo(
            Const(BTN_ADMIN_EXTEND),
            id="extend",
            state=AdminSG.users_extend,
            when=F["has_user"],
        ),
        Button(
            Const(BTN_ADMIN_REVOKE),
            id="revoke",
            on_click=revoke_user_subscription,
            when=F["has_user"],
        ),
        SwitchTo(
            Const(BTN_ADMIN_FIND_ANOTHER),
            id="find_another",
            state=AdminSG.users_search,
        ),
        state=AdminSG.users_card,
        getter=user_card_getter,
    ),

    # ---- Users: extend ----
    Window(
        Const(ADMIN_EXTEND_PROMPT),
        MessageInput(
            func=extend_date_handler,
            content_types=[ContentType.TEXT],
        ),
        Back(Const(BTN_BACK)),
        state=AdminSG.users_extend,
    ),

    # ---- Statistics ----
    Window(
        Format("{stats}"),
        SwitchTo(
            Const(BTN_BACK),
            id="statistic_back",
            state=AdminSG.adminpanel,
        ),
        state=AdminSG.statistic,
        getter=stats_getter,
    ),
)
