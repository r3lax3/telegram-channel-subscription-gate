from aiogram.types import CallbackQuery

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Select

from tgbot.states import UserSG


async def on_tariff_selected(
    callback: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
) -> None:
    manager.dialog_data["tariff_months"] = int(item_id)
    await manager.switch_to(UserSG.payment_link)
