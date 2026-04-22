import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from core.services.subscription import SubscriptionService
from core.services.payment import PaymentService
from infrastructure.database.models import User, Payment


@pytest.mark.asyncio
class TestSubscriptionService:
    async def test_activate_subscription_new_user(self, uow, mock_bot, settings):
        service = SubscriptionService(uow, mock_bot, settings)
        invite_link = await service.activate_subscription(111111, "alice")

        assert invite_link == "https://t.me/+test_invite_link"
        mock_bot.create_chat_invite_link.assert_called_once_with(
            chat_id=settings.channel_id,
            member_limit=1,
        )

        user = await uow.users.get_by_telegram_id(111111)
        assert user is not None
        assert user.is_active is True
        assert user.subscription_end_date is not None
        expected_end = datetime.utcnow() + timedelta(days=30)
        assert abs((user.subscription_end_date - expected_end).total_seconds()) < 5

    async def test_activate_subscription_extends_existing(self, uow, mock_bot, settings):
        # Create user with existing active subscription
        user = await uow.users.get_or_create(222222, "bob")
        future_date = datetime.utcnow() + timedelta(days=10)
        user.subscription_end_date = future_date
        user.is_active = True
        await uow.users.update(user)
        await uow.commit()

        service = SubscriptionService(uow, mock_bot, settings)
        await service.activate_subscription(222222, "bob")

        user = await uow.users.get_by_telegram_id(222222)
        expected_end = future_date + timedelta(days=30)
        assert abs((user.subscription_end_date - expected_end).total_seconds()) < 5

    async def test_kick_user(self, uow, mock_bot, settings):
        service = SubscriptionService(uow, mock_bot, settings)
        await service.kick_user(111111)

        mock_bot.ban_chat_member.assert_called_once_with(settings.channel_id, 111111)
        mock_bot.unban_chat_member.assert_called_once_with(
            settings.channel_id, 111111, only_if_banned=True
        )

    async def test_get_expiring_users(self, uow, mock_bot, settings):
        user = await uow.users.get_or_create(333333, "carol")
        user.is_active = True
        user.subscription_end_date = datetime.utcnow() + timedelta(days=2)
        await uow.users.update(user)
        await uow.commit()

        service = SubscriptionService(uow, mock_bot, settings)
        expiring = await service.get_expiring_users(days=3)
        assert len(expiring) == 1

    async def test_get_expired_users(self, uow, mock_bot, settings):
        user = await uow.users.get_or_create(444444, "dave")
        user.is_active = True
        user.subscription_end_date = datetime.utcnow() - timedelta(hours=1)
        await uow.users.update(user)
        await uow.commit()

        service = SubscriptionService(uow, mock_bot, settings)
        expired = await service.get_expired_users()
        assert len(expired) == 1


@pytest.mark.asyncio
class TestPaymentService:
    async def test_create_payment_link(self, uow, settings):
        service = PaymentService(uow, settings)

        with patch(
            "infrastructure.prodamus.client.ProdamusClient.create_payment_link",
            new_callable=AsyncMock,
            return_value="https://test.payform.ru/?order_id=test",
        ):
            link = await service.create_payment_link(111111, "alice")

        assert "payform.ru" in link
        user = await uow.users.get_by_telegram_id(111111)
        assert user is not None

    async def test_process_webhook_success(self, uow, settings):
        # Create user and payment first
        user = await uow.users.get_or_create(222222, "bob")
        await uow.commit()

        payment = Payment(
            id=2000000001,
            user_id=user.id,
            amount=1234,
            status="pending",
        )
        await uow.payments.create(payment)
        await uow.commit()

        service = PaymentService(uow, settings)
        result = await service.process_webhook({"order_id": "2000000001"})

        assert result is True
        updated = await uow.payments.get_by_order_id(2000000001)
        assert updated.status == "success"

    async def test_process_webhook_already_processed(self, uow, settings):
        user = await uow.users.get_or_create(333333, "carol")
        await uow.commit()

        payment = Payment(
            id=2000000002,
            user_id=user.id,
            amount=1234,
            status="success",
        )
        await uow.payments.create(payment)
        await uow.commit()

        service = PaymentService(uow, settings)
        result = await service.process_webhook({"order_id": "2000000002"})

        assert result is False

    async def test_process_webhook_not_found(self, uow, settings):
        service = PaymentService(uow, settings)
        result = await service.process_webhook({"order_id": "9999999999"})
        assert result is False

    async def test_process_webhook_no_order_id(self, uow, settings):
        service = PaymentService(uow, settings)
        result = await service.process_webhook({})
        assert result is False
