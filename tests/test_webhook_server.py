import hashlib
import hmac

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, TestClient, TestServer
from unittest.mock import AsyncMock, MagicMock, patch

from infrastructure.webhook.server import WebhookServer


@pytest_asyncio.fixture
async def webhook_app(settings, session_factory, mock_bot):
    server = WebhookServer(
        settings=settings,
        session_factory=session_factory,
        bot=mock_bot,
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

    async def test_webhook_invalid_signature(self, client):
        resp = await client.post(
            "/prodamus/webhook",
            data={"order_id": "123", "customer_extra": "111"},
            headers={"Sign": "invalid"},
        )
        assert resp.status == 403

    async def test_webhook_missing_customer_extra(self, client, settings):
        data = {"order_id": "123", "customer_extra": "0"}
        sorted_items = sorted(data.items())
        check_string = "&".join(f"{k}={v}" for k, v in sorted_items)
        signature = hmac.new(
            settings.prodamus_secret_key.encode(),
            check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        resp = await client.post(
            "/prodamus/webhook",
            data=data,
            headers={"Sign": signature},
        )
        assert resp.status == 400

    async def test_webhook_valid_request(self, client, settings, uow):
        # Create a user and payment first
        from infrastructure.database.models import Payment

        user = await uow.users.get_or_create(111111, "test")
        await uow.commit()

        payment = Payment(
            user_id=user.id,
            amount=1234,
            status="pending",
            prodamus_order_id="webhook_order_1",
        )
        await uow.payments.create(payment)
        await uow.commit()

        data = {"order_id": "webhook_order_1", "customer_extra": "111111"}
        sorted_items = sorted(data.items())
        check_string = "&".join(f"{k}={v}" for k, v in sorted_items)
        signature = hmac.new(
            settings.prodamus_secret_key.encode(),
            check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        resp = await client.post(
            "/prodamus/webhook",
            data=data,
            headers={"Sign": signature},
        )
        assert resp.status == 200
