import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from aiohttp.test_utils import TestClient, TestServer

from infrastructure.webhook.server import WebhookServer


@pytest_asyncio.fixture
async def webhook_app(settings, session_factory, mock_bot):
    bg_manager = MagicMock()
    bg_manager.bg.return_value = AsyncMock()
    server = WebhookServer(
        settings=settings,
        session_factory=session_factory,
        bot=mock_bot,
        bg_manager_factory=bg_manager,
    )
    return server.app


@pytest_asyncio.fixture
async def client(webhook_app):
    async with TestClient(TestServer(webhook_app)) as client:
        yield client


@pytest.mark.asyncio
class TestWebhookEndpoints:
    async def test_health_check(self, client):
        resp = await client.get("/health")
        assert resp.status == 200
        text = await resp.text()
        assert text == "OK"

    async def test_webhook_non_success_status_returns_ok(self, client):
        resp = await client.post(
            "/prodamus/webhook",
            data={
                "order_id": "123",
                "customer_extra": "111111",
                "payment_status": "pending",
            },
        )
        assert resp.status == 200

    async def test_webhook_unknown_payment_returns_ok(self, client):
        resp = await client.post(
            "/prodamus/webhook",
            data={
                "order_id": "999",
                "customer_extra": "0",
                "payment_status": "success",
            },
        )
        assert resp.status == 200

    async def test_webhook_valid_request(self, client, uow):
        from infrastructure.database.models import Payment

        user = await uow.users.get_or_create(111111, "test")
        await uow.commit()

        payment = Payment(
            id=3000000001,
            user_id=user.id,
            amount=2000,
            days=30,
            status="pending",
        )
        await uow.payments.create(payment)
        await uow.commit()

        resp = await client.post(
            "/prodamus/webhook",
            data={
                "order_id": "3000000001",
                "customer_extra": "111111",
                "payment_status": "success",
            },
        )
        assert resp.status == 200

    async def test_webhook_activates_for_paid_days(self, client, uow, session):
        from datetime import datetime, timedelta, timezone

        from infrastructure.database.models import Payment

        user = await uow.users.get_or_create(222333, "quarter")
        await uow.commit()

        payment = Payment(
            id=3000000002,
            user_id=user.id,
            amount=4050,
            days=90,
            status="pending",
        )
        await uow.payments.create(payment)
        await uow.commit()

        resp = await client.post(
            "/prodamus/webhook",
            data={
                "order_id": "3000000002",
                "customer_extra": "222333",
                "payment_status": "success",
            },
        )
        assert resp.status == 200

        session.expire_all()
        user = await uow.users.get_by_telegram_id(222333)
        assert user.is_active is True
        expected_end = (
            datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=90)
        )
        assert abs((user.subscription_end_date - expected_end).total_seconds()) < 10
