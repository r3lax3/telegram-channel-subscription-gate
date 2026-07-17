import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from core.services.subscription import SubscriptionService
from core.services.payment import PaymentService
from core.services.pricing import TARIFFS, get_tariff, monthly_price, tariff_price
from infrastructure.database.models import User, Payment


class TestPricing:
    def test_legacy_prices(self):
        assert [tariff_price(1500, t) for t in TARIFFS] == [1500, 4050, 7650]

    def test_new_client_prices(self):
        assert [tariff_price(2000, t) for t in TARIFFS] == [2000, 5400, 10200]

    def test_monthly_price(self, settings):
        assert monthly_price(settings, legacy=True) == 1500
        assert monthly_price(settings, legacy=False) == 2000

    def test_get_tariff(self):
        assert get_tariff(3).days == 90
        assert get_tariff(6).discount_percent == 15
        assert get_tariff(2) is None


@pytest.mark.asyncio
class TestSubscriptionService:
    async def test_activate_subscription_new_user(self, uow, mock_bot, settings):
        service = SubscriptionService(uow, mock_bot, settings)
        user = await service.activate_subscription(111111, "alice", days=30)

        assert user.telegram_id == 111111
        assert user.is_active is True
        mock_bot.create_chat_invite_link.assert_not_called()

        fetched = await uow.users.get_by_telegram_id(111111)
        assert fetched is not None
        assert fetched.is_active is True
        assert fetched.subscription_end_date is not None
        expected_end = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)
        assert abs((fetched.subscription_end_date - expected_end).total_seconds()) < 5

    async def test_activate_subscription_extends_existing(self, uow, mock_bot, settings):
        # Create user with existing active subscription
        user = await uow.users.get_or_create(222222, "bob")
        future_date = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=10)
        user.subscription_end_date = future_date
        user.is_active = True
        await uow.users.update(user)
        await uow.commit()

        service = SubscriptionService(uow, mock_bot, settings)
        await service.activate_subscription(222222, "bob", days=90)

        user = await uow.users.get_by_telegram_id(222222)
        expected_end = future_date + timedelta(days=90)
        assert abs((user.subscription_end_date - expected_end).total_seconds()) < 5

    async def test_is_legacy_client(self, uow, mock_bot, settings):
        user = await uow.users.get_or_create(777777, "grace")
        user.is_active = True
        user.subscription_end_date = (
            datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=5)
        )

        # решает только флаг: он сбрасывается при разрыве подписки
        # и управляется из админки
        user.legacy_pricing = True
        assert SubscriptionService.is_legacy_client(user) is True

        user.legacy_pricing = False
        assert SubscriptionService.is_legacy_client(user) is False

        assert SubscriptionService.is_legacy_client(None) is False

    async def test_set_legacy_pricing(self, uow, mock_bot, settings):
        await uow.users.get_or_create(999999, "ivan")
        await uow.commit()

        service = SubscriptionService(uow, mock_bot, settings)
        user = await service.set_legacy_pricing(999999, True)
        assert user.legacy_pricing is True

        user = await service.set_legacy_pricing(999999, False)
        assert user.legacy_pricing is False

        assert await service.set_legacy_pricing(123, True) is None

    async def test_revoke_clears_legacy_flag(self, uow, mock_bot, settings):
        user = await uow.users.get_or_create(888888, "heidi")
        user.is_active = True
        user.legacy_pricing = True
        user.subscription_end_date = (
            datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=5)
        )
        await uow.users.update(user)
        await uow.commit()

        service = SubscriptionService(uow, mock_bot, settings)
        await service.revoke_subscription(888888)

        user = await uow.users.get_by_telegram_id(888888)
        assert user.legacy_pricing is False

    async def test_kick_user(self, uow, mock_bot, settings):
        service = SubscriptionService(uow, mock_bot, settings)
        result = await service.kick_user(111111)

        assert result is True
        mock_bot.ban_chat_member.assert_called_once_with(settings.channel_id, 111111)
        mock_bot.unban_chat_member.assert_called_once_with(
            settings.channel_id, 111111, only_if_banned=True
        )

    async def test_kick_user_failure_returns_false(self, uow, mock_bot, settings):
        mock_bot.ban_chat_member.side_effect = RuntimeError("no rights")
        service = SubscriptionService(uow, mock_bot, settings)
        result = await service.kick_user(111111)

        assert result is False

    async def test_get_expiring_users(self, uow, mock_bot, settings):
        user = await uow.users.get_or_create(333333, "carol")
        user.is_active = True
        user.subscription_end_date = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)
        await uow.users.update(user)
        await uow.commit()

        service = SubscriptionService(uow, mock_bot, settings)
        expiring = await service.get_expiring_users(days=3)
        assert len(expiring) == 1

    async def test_get_expired_users(self, uow, mock_bot, settings):
        user = await uow.users.get_or_create(444444, "dave")
        user.is_active = True
        user.subscription_end_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
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
            order_id, link = await service.create_payment_link(
                111111, "alice", amount=2000, days=30
            )

        assert isinstance(order_id, int)
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

        assert result is not None
        assert result.id == 2000000001
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

        assert result is None

    async def test_process_webhook_not_found(self, uow, settings):
        service = PaymentService(uow, settings)
        result = await service.process_webhook({"order_id": "9999999999"})
        assert result is None

    async def test_process_webhook_no_order_id(self, uow, settings):
        service = PaymentService(uow, settings)
        result = await service.process_webhook({})
        assert result is None

    async def test_process_webhook_falls_back_to_customer_extra(self, uow, settings):
        # When Prodamus webhook is missing our order_id, we should still
        # resolve the pending payment via customer_extra (telegram_id).
        user = await uow.users.get_or_create(555555, "erin")
        await uow.commit()

        payment = Payment(
            id=2000000003,
            user_id=user.id,
            amount=1234,
            status="pending",
        )
        await uow.payments.create(payment)
        await uow.commit()

        service = PaymentService(uow, settings)
        result = await service.process_webhook(
            {"customer_extra": "555555", "order_num": "43957840"}
        )

        assert result is not None
        assert result.id == 2000000003
        updated = await uow.payments.get_by_order_id(2000000003)
        assert updated.status == "success"
