#!/usr/bin/env python3
"""
Отправляет тестовый вебхук об успешной оплате на продакшн-хендлер.

Перед запуском задай нужные значения в переменных ниже.
"""

import urllib.request
import urllib.parse
import json

# ─── Параметры ────────────────────────────────────────────────────────────────

ORDER_ID = "12345"          # ID платежа (Payment.id в нашей БД)
CUSTOMER_EXTRA = "111111"   # Telegram ID пользователя
WEBHOOK_URL = "https://apps.r3lax3.site/astrobot/prodamus/webhook"

# ──────────────────────────────────────────────────────────────────────────────

payload = {
    "order_id": ORDER_ID,
    "customer_extra": CUSTOMER_EXTRA,
    "payment_status": "success",
}

data = urllib.parse.urlencode(payload).encode("utf-8")

req = urllib.request.Request(
    WEBHOOK_URL,
    data=data,
    method="POST",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

print(f"Отправляю вебхук на {WEBHOOK_URL}")
print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
print()

with urllib.request.urlopen(req, timeout=10) as resp:
    body = resp.read().decode("utf-8")
    print(f"Статус: {resp.status}")
    print(f"Ответ:  {body}")
