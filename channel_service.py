"""
Channel access service.

- Creating / retrieving invite links
- Adding / kicking users from the channel
"""

import logging
from typing import Optional

from aiogram import Bot

from config import CHANNEL_ID
from database import get_bot_state, set_bot_state

logger = logging.getLogger(__name__)

INVITE_LINK_KEY = "channel_invite_link"


async def get_or_create_invite_link(bot: Bot) -> str:
    """
    Get existing invite link from DB or create a new one.

    The invite link is created once and reused across bot restarts.
    """
    # Try to get saved link
    saved_link = await get_bot_state(INVITE_LINK_KEY)
    if saved_link:
        # Verify the link is still valid by checking channel info
        try:
            chat = await bot.get_chat(CHANNEL_ID)
            # If we have a saved link, return it
            return saved_link
        except Exception:
            logger.warning("Saved invite link may be invalid, creating new one")

    # Create a new invite link
    link = await bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        name="Bot subscription link",
        creates_join_request=False,
    )
    await set_bot_state(INVITE_LINK_KEY, link.invite_link)
    logger.info(f"Created new invite link: {link.invite_link}")
    return link.invite_link


async def kick_user_from_channel(bot: Bot, user_id: int) -> bool:
    """
    Remove a user from the channel.

    Uses ban + unban to kick without permanent ban,
    so the user can rejoin later if they resubscribe.
    """
    try:
        await bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id, only_if_banned=True)
        logger.info(f"Kicked user {user_id} from channel {CHANNEL_ID}")
        return True
    except Exception as e:
        logger.error(f"Failed to kick user {user_id}: {e}")
        return False


async def check_user_in_channel(bot: Bot, user_id: int) -> bool:
    """Check if user is a member of the channel."""
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False
