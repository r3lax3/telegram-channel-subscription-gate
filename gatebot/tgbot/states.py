from aiogram.fsm.state import StatesGroup, State


class UserSG(StatesGroup):
    main_menu = State()

    payment_menu = State()
    payment_success = State()


class AdminSG(StatesGroup):
    adminpanel = State()

    broadcast_menu = State()
    broadcast_add_button_get_text = State()

    statistic = State()
