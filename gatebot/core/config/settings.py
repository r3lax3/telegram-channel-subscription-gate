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
    subscription_price: int = 1234
    subscription_days: int = 30

    # Early-bird pricing: users whose first successful payment happened before
    # the deadline keep early_bird_price forever (renewals included). Before
    # the deadline everyone pays early_bird_price. Unset deadline disables the
    # feature entirely: everyone pays subscription_price.
    early_bird_price: int = 1500
    early_bird_deadline: datetime | None = None

    @field_validator("early_bird_deadline")
    @classmethod
    def _deadline_to_naive_utc(cls, v: datetime | None) -> datetime | None:
        # DB timestamps are naive UTC (see core.utils.utcnow); normalize a
        # tz-aware deadline so comparisons don't raise.
        if v is not None and v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        return v

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
