import hashlib
import hmac
from urllib.parse import urlencode

from core.config.settings import Settings


class ProdamusClient:
    def __init__(self, settings: Settings) -> None:
        self.domain = settings.prodamus_domain
        self.secret = settings.prodamus_secret_key

    async def create_payment_link(
        self, order_id: str, amount: int, customer_extra: str
    ) -> str:
        params = {
            "order_id": order_id,
            "customer_extra": customer_extra,
            "products[0][name]": "Подписка на канал",
            "products[0][price]": str(amount),
            "products[0][quantity]": "1",
            "do": "link",
        }
        url = f"https://{self.domain}/?{urlencode(params)}"
        return url

    @staticmethod
    def verify_signature(data: dict, signature: str, secret: str) -> bool:
        sorted_items = sorted(data.items())
        check_string = "&".join(f"{k}={v}" for k, v in sorted_items)
        expected = hmac.new(
            secret.encode(), check_string.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
