import hashlib
import hmac

import pytest

from infrastructure.prodamus.client import ProdamusClient


class TestProdamusClient:
    def test_verify_signature_valid(self):
        data = {"order_id": "123", "amount": "1000"}
        secret = "test_secret"

        sorted_items = sorted(data.items())
        check_string = "&".join(f"{k}={v}" for k, v in sorted_items)
        signature = hmac.new(
            secret.encode(), check_string.encode(), hashlib.sha256
        ).hexdigest()

        assert ProdamusClient.verify_signature(data, signature, secret) is True

    def test_verify_signature_invalid(self):
        data = {"order_id": "123", "amount": "1000"}
        assert ProdamusClient.verify_signature(data, "invalid_sig", "secret") is False

    @pytest.mark.asyncio
    async def test_create_payment_link(self, settings):
        client = ProdamusClient(settings)
        link = await client.create_payment_link(
            order_id="test_order",
            amount=1234,
            customer_extra="111111",
        )

        assert settings.prodamus_domain in link
        assert "test_order" in link
        assert "111111" in link


class TestProdamusClientInit:
    def test_init(self, settings):
        client = ProdamusClient(settings)
        assert client.domain == settings.prodamus_domain
        assert client.secret == settings.prodamus_secret_key
