from aiogram.fsm.state import StatesGroup, State


class UserSG(StatesGroup):
    main_menu = State()
    payment_menu = State()
    subscription_active = State()


class AdminSG(StatesGroup):
    adminpanel = State()

    broadcast_menu = State()

    users_search = State()
    users_card = State()
    users_extend = State()

    statistic = State()
