"""
Prodamus payment integration.

- Generating payment links
- Verifying webhook signatures
- Recurring (auto-renewal) payments
"""

import hashlib
import hmac
import json
import uuid
from typing import Optional
from urllib.parse import urlencode

import aiohttp

from config import (
    PRODAMUS_API_KEY,
    PRODAMUS_DOMAIN,
    PRODAMUS_SECRET_KEY,
    SUBSCRIPTION_PRICE,
    WEBHOOK_PATH,
)


def generate_order_id(user_id: int) -> str:
    """Generate a unique order ID."""
    return f"sub_{user_id}_{uuid.uuid4().hex[:8]}"


def create_payment_link(
    order_id: str,
    user_id: int,
    amount: Optional[int] = None,
    customer_email: str = "",
    customer_phone: str = "",
) -> str:
    """
    Create a Prodamus payment link.

    Prodamus accepts payment via a URL with query parameters.
    """
    if amount is None:
        amount = SUBSCRIPTION_PRICE

    params = {
        "order_id": order_id,
        "products[0][name]": "Подписка на закрытый канал (30 дней)",
        "products[0][price]": str(amount),
        "products[0][quantity]": "1",
        "do": "link",
        "customer_extra": str(user_id),
        "subscription": "1",  # Enable recurring payments
    }

    if customer_email:
        params["customer_email"] = customer_email
    if customer_phone:
        params["customer_phone"] = customer_phone

    # Build the payment URL
    base_url = f"https://{PRODAMUS_DOMAIN}/payment"
    return f"{base_url}?{urlencode(params)}"


def verify_webhook_signature(data: dict, signature: str) -> bool:
    """
    Verify the Prodamus webhook signature.

    Prodamus signs webhooks with HMAC-SHA256 using the secret key.
    The data fields are sorted alphabetically, concatenated, and signed.
    """
    if not PRODAMUS_SECRET_KEY:
        return True  # Skip verification if no secret key configured

    def normalize_value(val):
        if isinstance(val, dict):
            return {k: normalize_value(v) for k, v in sorted(val.items())}
        if isinstance(val, list):
            return [normalize_value(v) for v in val]
        return str(val)

    normalized = normalize_value(data)
    json_str = json.dumps(normalized, separators=(",", ":"), ensure_ascii=False)

    expected = hmac.new(
        PRODAMUS_SECRET_KEY.encode("utf-8"),
        json_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


async def charge_recurring(recurring_token: str, order_id: str, amount: Optional[int] = None) -> dict:
    """
    Attempt a recurring (auto-renewal) payment using a saved token.

    Returns the Prodamus API response.
    """
    if amount is None:
        amount = SUBSCRIPTION_PRICE

    url = f"https://{PRODAMUS_DOMAIN}/api/v1/recurring"
    payload = {
        "token": recurring_token,
        "order_id": order_id,
        "products": [
            {
                "name": "Автопродление подписки (30 дней)",
                "price": str(amount),
                "quantity": "1",
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {PRODAMUS_API_KEY}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            result = await resp.json()
            result["http_status"] = resp.status
            return result
