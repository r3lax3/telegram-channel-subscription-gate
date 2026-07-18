from datetime import datetime, timezone

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    debug: bool = False

    database_url: str
    redis_url: str
    bot_token: str
    owner_ids: list[int]

    support_link: str

    channel_id: int
    # Базовая цена руб/месяц; цены тарифов (квартал, полгода) считаются от неё
    subscription_price: int = 2000
    # Цена для «старичков» — непрерывная подписка, оплаченная до даты отсечки
    subscription_price_legacy: int = 1500
    # Дата окончания акции «успей купить по старой цене». Пока текущий момент
    # раньше неё, все видят и платят subscription_price_legacy, а оплатившие
    # получают флаг legacy_pricing. Пусто — акция выключена. Хранится как
    # naive UTC; значение с таймзоной (2026-07-31T00:00:00+03:00) нормализуется.
    legacy_promo_until: datetime | None = None

    @field_validator("legacy_promo_until", mode="before")
    @classmethod
    def _empty_promo_until_is_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("legacy_promo_until", mode="after")
    @classmethod
    def _promo_until_to_naive_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    prodamus_domain: str = ""
    prodamus_secret_key: str = ""
    bot_link: str = ""

    webhook_host: str = ""
    webhook_port: int = 8080

    invite_link_file: str = "/app/data/invite_link.txt"
    invite_link_name: str = "gatebot"

    # Astrobot subscription sync (optional)
    astrobot_sync_enabled: bool = False
    astrobot_sync_url: str = ""
    astrobot_sync_secret: str = ""
