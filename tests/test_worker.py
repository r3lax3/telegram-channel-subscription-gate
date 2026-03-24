import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from core.services.worker import subscription_worker


@pytest.mark.asyncio
class TestSubscriptionWorker:
    async def test_worker_notifies_expiring_users(
        self, session_factory, mock_bot, settings, uow
    ):
        # Create expiring user
        user = await uow.users.get_or_create(111111, "expiring_user")
        user.is_active = True
        user.subscription_end_date = datetime.utcnow() + timedelta(days=2)
        await uow.users.update(user)
        await uow.commit()

        # Patch sleep to stop after one iteration
        with patch("core.services.worker.asyncio.sleep", side_effect=asyncio.CancelledError):
            with pytest.raises(asyncio.CancelledError):
                await subscription_worker(session_factory, mock_bot, settings)

        # Bot should have sent a message to expiring user
        mock_bot.send_message.assert_called()
        calls = mock_bot.send_message.call_args_list
        tg_ids = [call.args[0] for call in calls]
        assert 111111 in tg_ids

    async def test_worker_kicks_expired_users(
        self, session_factory, mock_bot, settings, uow
    ):
        # Create expired user
        user = await uow.users.get_or_create(222222, "expired_user")
        user.is_active = True
        user.subscription_end_date = datetime.utcnow() - timedelta(hours=1)
        await uow.users.update(user)
        await uow.commit()

        with patch("core.services.worker.asyncio.sleep", side_effect=asyncio.CancelledError):
            with pytest.raises(asyncio.CancelledError):
                await subscription_worker(session_factory, mock_bot, settings)

        mock_bot.ban_chat_member.assert_called_with(settings.channel_id, 222222)
        mock_bot.unban_chat_member.assert_called_with(
            settings.channel_id, 222222, only_if_banned=True
        )

    async def test_worker_handles_errors_gracefully(
        self, session_factory, mock_bot, settings, uow
    ):
        # Create expired user but make bot.ban raise an error
        user = await uow.users.get_or_create(333333, "error_user")
        user.is_active = True
        user.subscription_end_date = datetime.utcnow() - timedelta(hours=1)
        await uow.users.update(user)
        await uow.commit()

        mock_bot.ban_chat_member.side_effect = Exception("API error")

        with patch("core.services.worker.asyncio.sleep", side_effect=asyncio.CancelledError):
            with pytest.raises(asyncio.CancelledError):
                await subscription_worker(session_factory, mock_bot, settings)

        # Worker should not crash - CancelledError from sleep means it completed one iteration
