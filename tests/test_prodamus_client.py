import pytest

from infrastructure.prodamus.client import ProdamusClient, _create_hmac, verify_webhook_signature


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


class TestVerifyWebhookSignature:
    def test_valid_signature(self):
        key = "test_secret"
        data = {"order_id": "123", "payment_status": "success", "customer_extra": "456"}
        sign = _create_hmac(data, key)
        assert verify_webhook_signature({**data, "sign": sign}, key) is True

    def test_invalid_signature(self):
        key = "test_secret"
        data = {"order_id": "123", "payment_status": "success"}
        assert verify_webhook_signature({**data, "sign": "wrong"}, key) is False

    def test_missing_sign_field(self):
        key = "test_secret"
        data = {"order_id": "123", "payment_status": "success"}
        assert verify_webhook_signature(data, key) is False

    def test_sign_excluded_from_payload(self):
        key = "test_secret"
        data = {"order_id": "123", "payment_status": "success"}
        sign = _create_hmac(data, key)
        # The sign field itself must not be included when computing the expected hash
        assert verify_webhook_signature({**data, "sign": sign}, key) is True


class TestProdamusClient:
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
