"""
Telegram bot handlers: /start, payment menu, support.
"""

import logging

from aiogram import Bot, Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from config import SUBSCRIPTION_PRICE
from database import upsert_user, get_active_subscription, create_payment
from channel_service import get_or_create_invite_link
from prodamus import generate_order_id, create_payment_link
import texts

logger = logging.getLogger(__name__)

router = Router()


def start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.BTN_PAY)],
            [KeyboardButton(text=texts.BTN_SUPPORT)],
        ],
        resize_keyboard=True,
    )


def payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=texts.BTN_PROCEED_PAYMENT, url=payment_url)],
            [InlineKeyboardButton(text=texts.BTN_BACK, callback_data="back_to_start")],
        ]
    )


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    """Handle /start command — show welcome message."""
    await upsert_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    # Check if user already has an active subscription
    sub = await get_active_subscription(message.from_user.id)
    if sub:
        invite_link = await get_or_create_invite_link(bot)
        await message.answer(
            texts.ALREADY_SUBSCRIBED.format(
                expires_at=sub["expires_at"],
                invite_link=invite_link,
            ),
            parse_mode="HTML",
            reply_markup=start_keyboard(),
        )
        return

    await message.answer(
        texts.START_MESSAGE,
        reply_markup=start_keyboard(),
    )


@router.message(F.text == texts.BTN_PAY)
async def handle_pay_button(message: Message, bot: Bot):
    """Show payment menu with price info and payment link."""
    user_id = message.from_user.id

    # Check if already subscribed
    sub = await get_active_subscription(user_id)
    if sub:
        invite_link = await get_or_create_invite_link(bot)
        await message.answer(
            texts.ALREADY_SUBSCRIBED.format(
                expires_at=sub["expires_at"],
                invite_link=invite_link,
            ),
            parse_mode="HTML",
        )
        return

    # Generate order and payment link
    order_id = generate_order_id(user_id)
    await create_payment(user_id, order_id, SUBSCRIPTION_PRICE)
    payment_url = create_payment_link(order_id=order_id, user_id=user_id)

    await message.answer(
        texts.PAYMENT_MENU_MESSAGE,
        parse_mode="HTML",
        reply_markup=payment_keyboard(payment_url),
    )


@router.callback_query(F.data == "back_to_start")
async def handle_back_to_start(callback: CallbackQuery):
    """Return to start menu."""
    await callback.message.delete()
    await callback.message.answer(
        texts.START_MESSAGE,
        reply_markup=start_keyboard(),
    )
    await callback.answer()


@router.message(F.text == texts.BTN_SUPPORT)
async def handle_support(message: Message):
    """Show support info."""
    await message.answer(texts.SUPPORT_MESSAGE)
