import logging
from datetime import datetime

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ContentType

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput

from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from tgbot.states import AdminSG
from tgbot.texts import (
    ADMIN_BROADCAST_DONE,
    ADMIN_BROADCAST_EMPTY,
    ADMIN_EXTEND_BAD_DATE,
    ADMIN_EXTEND_DONE,
    ADMIN_REVOKE_DONE,
    ADMIN_USER_NOT_FOUND,
)
from core.interfaces.repositories.uow import UnitOfWork
from core.services.subscription import SubscriptionService


logger = logging.getLogger(__name__)


@inject
async def approve_broadcast(
    callback: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    uow: FromDishka[UnitOfWork],
    bot: FromDishka[Bot],
):
    broadcast_text = manager.dialog_data.get("broadcast_text")
    broadcast_photo_file_id = manager.dialog_data.get("broadcast_photo_file_id")

    if not broadcast_text and not broadcast_photo_file_id:
        await callback.answer(ADMIN_BROADCAST_EMPTY)
        return

    users = await uow.users.get_all_users()
    ok = 0
    failed = 0
    for user in users:
        try:
            if broadcast_photo_file_id:
                await bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=broadcast_photo_file_id,
                    caption=broadcast_text,
                )
            else:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=broadcast_text,
                )
            ok += 1
        except Exception:
            failed += 1

    await callback.answer(ADMIN_BROADCAST_DONE.format(ok=ok, failed=failed), show_alert=True)

    manager.dialog_data.pop("broadcast_text", None)
    manager.dialog_data.pop("broadcast_photo_file_id", None)
    manager.dialog_data["have_broadcast_content"] = False


async def clear_broadcast_content(
    callback: CallbackQuery,
    widget: Button,
    manager: DialogManager,
):
    manager.dialog_data.pop("broadcast_text", None)
    manager.dialog_data.pop("broadcast_photo_file_id", None)
    manager.dialog_data["have_broadcast_content"] = False
    await callback.answer("ok")


async def broadcast_content_handler(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
):
    if message.photo:
        manager.dialog_data["broadcast_photo_file_id"] = message.photo[-1].file_id
        manager.dialog_data["broadcast_text"] = message.caption
    elif message.content_type == ContentType.TEXT:
        manager.dialog_data["broadcast_text"] = message.text
        manager.dialog_data.pop("broadcast_photo_file_id", None)

    manager.dialog_data["have_broadcast_content"] = True


@inject
async def user_search_handler(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
    uow: FromDishka[UnitOfWork],
):
    query = (message.text or "").strip()
    if not query:
        await message.answer(ADMIN_USER_NOT_FOUND)
        return

    user = None
    if query.lstrip("-").isdigit():
        user = await uow.users.get_by_telegram_id(int(query))
    if user is None:
        user = await uow.users.get_by_username(query)

    if user is None:
        await message.answer(ADMIN_USER_NOT_FOUND)
        return

    manager.dialog_data["selected_telegram_id"] = user.telegram_id
    await manager.switch_to(AdminSG.users_card)


@inject
async def revoke_user_subscription(
    callback: CallbackQuery,
    widget: Button,
    manager: DialogManager,
    subscription_service: FromDishka[SubscriptionService],
):
    telegram_id = manager.dialog_data.get("selected_telegram_id")
    if not telegram_id:
        await callback.answer(ADMIN_USER_NOT_FOUND)
        return
    user = await subscription_service.revoke_subscription(int(telegram_id))
    if user is None:
        await callback.answer(ADMIN_USER_NOT_FOUND)
        return
    await callback.answer(ADMIN_REVOKE_DONE, show_alert=True)


@inject
async def extend_date_handler(
    message: Message,
    widget: MessageInput,
    manager: DialogManager,
    subscription_service: FromDishka[SubscriptionService],
):
    raw = (message.text or "").strip()
    try:
        new_date = datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        await message.answer(ADMIN_EXTEND_BAD_DATE)
        return

    telegram_id = manager.dialog_data.get("selected_telegram_id")
    if not telegram_id:
        await message.answer(ADMIN_USER_NOT_FOUND)
        return

    user = await subscription_service.set_subscription_end(int(telegram_id), new_date)
    if user is None:
        await message.answer(ADMIN_USER_NOT_FOUND)
        return

    await message.answer(ADMIN_EXTEND_DONE.format(date=new_date.strftime("%Y-%m-%d")))
    await manager.switch_to(AdminSG.users_card)
