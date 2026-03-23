from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ContentType

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput

from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from tgbot.states import AdminSG
from core.interfaces.uow import UnitOfWork


@inject
async def approve_broadcast(
    callback: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    uow: FromDishka[UnitOfWork],
    bot: FromDishka[Bot]
):
    """Send broadcast to all users."""
    broadcast_text = manager.dialog_data.get("broadcast_text")
    broadcast_photo_file_id = manager.dialog_data.get("broadcast_photo_file_id")

    users = await uow.users.get_all_users()
    for user in users:
        try:
            if broadcast_photo_file_id:
                await bot.send_photo(
                    chat_id=user.id,
                    photo=broadcast_photo_file_id,
                    caption=broadcast_text
                )
            elif broadcast_text:
                await bot.send_message(
                    chat_id=user.id,
                    text=broadcast_text
                )
            else:
                await callback.answer("No broadcast data!")
                return

        except Exception:
            pass  # user blocked bot, etc.

    await callback.answer("Broadcast sent!")

    # Clear content after sending
    manager.dialog_data.pop("broadcast_text", None)
    manager.dialog_data.pop("broadcast_photo_file_id", None)

async def clear_broadcast_content(
    callback: CallbackQuery,
    widget: Button,
    manager: DialogManager
):
    """Clear broadcast content and stay on broadcast_menu."""
    manager.dialog_data.pop("broadcast_text", None)
    manager.dialog_data.pop("broadcast_photo_file_id", None)

    manager.dialog_data["have_broadcast_content"] = False

    await callback.answer("Broadcast content cleared!")


async def broadcast_content_handler(
    message: Message,
    widget: MessageInput,
    manager: DialogManager
):
    """Handle text message or photo (with optional caption) for broadcast."""
    if message.photo:
        manager.dialog_data["broadcast_photo_file_id"] = message.photo[-1].file_id
        manager.dialog_data["broadcast_text"] = message.caption  # Can be None

    elif message.content_type == ContentType.TEXT:
        manager.dialog_data["broadcast_text"] = message.text
        manager.dialog_data.pop("broadcast_photo_file_id", None)  # Clear photo if text-only

    manager.dialog_data["have_broadcast_content"] = True

