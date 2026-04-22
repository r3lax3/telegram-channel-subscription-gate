import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from urllib.parse import quote

import aiohttp

from core.config.settings import Settings

logger = logging.getLogger(__name__)

LINK_EXPIRATION_HOURS = 48


class ProdamusClient:
    def __init__(self, settings: Settings) -> None:
        self.domain = settings.prodamus_domain
        self.secret = settings.prodamus_secret_key
        self.bot_link = settings.bot_link

    async def create_payment_link(
        self,
        order_id: int,
        amount: int,
        customer_extra: int,
    ) -> str:
        expires_at = datetime.utcnow() + timedelta(hours=LINK_EXPIRATION_HOURS)

        params = {
            "do": "link",
            "products": [
                {
                    "name": "Подписка на канал",
                    "price": amount,
                    "quantity": 1,
                    "paymentMethod": 4,
                    "paymentObject": 4,
                }
            ],
            "order_id": order_id,
            "customer_extra": customer_extra,
            "link_expired": expires_at.strftime("%Y-%m-%d %H:%M"),
            "paid_content": self.bot_link,
            "sys": "",
        }

        signature = _create_hmac(params, self.secret)
        params["signature"] = signature

        query = _http_build_query(params)
        url = f"https://{self.domain}/?{query}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                payment_link = await resp.text()

        logger.info("Payment link created for order %s", order_id)
        return payment_link

    @staticmethod
    def verify_signature(data: dict, signature: str, secret: str) -> bool:
        expected = Hmac.create(data, secret)
        return hmac.compare_digest(expected, signature)


def _create_hmac(data: dict, key: str) -> str:
    normalized = _stringify_and_sort(data)
    data_str = json.dumps(
        normalized,
        separators=(",", ":"),
        ensure_ascii=False,
    ).replace("/", "\\/")
    return hmac.new(
        key.encode("utf-8"),
        data_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()



class Hmac:
    @staticmethod
    def create(data, key: str, algo='sha256'):
        # Приведение всех значений к строкам и сортировка
        data = Hmac._str_val_and_sort(data)
        # Подготовка строки для хэширования
        data_str = json.dumps(
            data,
            separators=(',', ':'),
            ensure_ascii=False
        ).replace('/', '\\/')

        data_binary = data_str.encode('utf-8')

        # Вычисление HMAC
        return hmac.new(
            key.encode('utf-8'),
            data_binary,
            algo
        ).hexdigest()

    @classmethod
    def _str_val_and_sort(cls, data):
        """Рекурсивно преобразует значения словаря в строки и сортирует ключи."""
        data = cls._sort_object(data)
        for item in list(data.keys()):
            if isinstance(data[item], dict):  # Если значение является словарем
                data[item] = cls._str_val_and_sort(data[item])
            elif isinstance(data[item], list):  # Если значение является списком
                # Преобразуем каждый элемент списка отдельно, если это необходимо
                data[item] = [
                    cls._str_val_and_sort(elem)
                    if isinstance(elem, dict)
                    else str(elem) for elem in data[item]
                ]
            else:
                data[item] = str(data[item])

        return data

    @classmethod
    def _sort_object(cls, obj):
        """Возвращает новый словарь с отсортированными ключами."""
        if not isinstance(obj, dict):
            return obj

        # Создаем новый словарь с тем же содержимым, но с отсортированными ключами
        sorted_obj = {key: obj[key] for key in sorted(obj)}  # python3.7 или выше
        return sorted_obj


def _stringify_and_sort(data):
    if isinstance(data, dict):
        return {k: _stringify_and_sort(v) for k, v in sorted(data.items())}
    if isinstance(data, list):
        return [_stringify_and_sort(item) for item in data]
    return str(data)


def _http_build_query(data: dict, prefix: str = "") -> str:
    parts: list[str] = []
    for key, value in data.items():
        full_key = f"{prefix}[{key}]" if prefix else str(key)
        if isinstance(value, dict):
            parts.append(_http_build_query(value, full_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                item_key = f"{full_key}[{i}]"
                if isinstance(item, dict):
                    parts.append(_http_build_query(item, item_key))
                else:
                    parts.append(f"{quote(item_key)}={quote(str(item))}")
        else:
            parts.append(f"{quote(full_key)}={quote(str(value))}")
    return "&".join(parts)
