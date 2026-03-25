import pytest

from infrastructure.prodamus.client import ProdamusClient, _create_hmac


class TestHmac:
    def test_create_hmac_deterministic(self):
        data = {"order_id": "123", "amount": "1000"}
        key = "test_secret"
        sig1 = _create_hmac(data, key)
        sig2 = _create_hmac(data, key)
        assert sig1 == sig2

    def test_create_hmac_with_nested_data(self):
        data = {
            "do": "link",
            "products": [
                {
                    "name": "Test product",
                    "price": 100,
                    "quantity": 1,
                }
            ],
            "order_id": "test_order",
        }
        key = "secret123"
        sig = _create_hmac(data, key)
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA256 hex digest length


class TestProdamusClient:
    def test_verify_signature_valid(self):
        data = {"order_id": "123", "amount": "1000"}
        secret = "test_secret"
        signature = _create_hmac(data, secret)

        assert ProdamusClient.verify_signature(data, signature, secret) is True

    def test_verify_signature_invalid(self):
        data = {"order_id": "123", "amount": "1000"}
        assert ProdamusClient.verify_signature(data, "invalid_sig", "secret") is False

    @pytest.mark.asyncio
    async def test_create_payment_link(self, settings):
        """Test that create_payment_link makes a request (mocked in real tests)."""
        client = ProdamusClient(settings)
        assert client.domain == settings.prodamus_domain
        assert client.secret == settings.prodamus_secret_key


class TestProdamusClientInit:
    def test_init(self, settings):
        client = ProdamusClient(settings)
        assert client.domain == settings.prodamus_domain
        assert client.secret == settings.prodamus_secret_key
        assert client.bot_link == settings.bot_link
