from datetime import datetime

import pytest

from core.config.settings import Settings


class TestSettings:
    def test_settings_from_kwargs(self, settings):
        assert settings.debug is True
        assert settings.bot_token == "test:token"
        assert settings.owner_ids == [12345678]
        assert settings.channel_id == -100123456789
        assert settings.subscription_price == 2000
        assert settings.subscription_price_legacy == 1500

    def test_settings_defaults(self, monkeypatch):
        # Clear env vars that .env file sets
        monkeypatch.delenv("debug", raising=False)
        monkeypatch.delenv("database_url", raising=False)
        monkeypatch.delenv("channel_id", raising=False)

        s = Settings(
            database_url="sqlite:///:memory:",
            redis_url="redis://localhost:6379",
            bot_token="test:token",
            owner_ids=[1],
            support_link="https://t.me/test",
            channel_id=-100123,
            _env_file=None,
        )
        assert s.debug is False
        assert s.subscription_price == 2000
        assert s.subscription_price_legacy == 1500
        assert s.webhook_port == 8080
        assert s.legacy_promo_until is None

    def test_legacy_promo_until_parsing(self):
        base = dict(
            database_url="sqlite:///:memory:",
            redis_url="redis://localhost:6379",
            bot_token="test:token",
            owner_ids=[1],
            support_link="https://t.me/test",
            channel_id=-100123,
            _env_file=None,
        )
        # Пустая строка из env = акция выключена
        s = Settings(legacy_promo_until="", **base)
        assert s.legacy_promo_until is None

        # Naive-дата хранится как есть (UTC)
        s = Settings(legacy_promo_until="2026-07-30 23:59:59", **base)
        assert s.legacy_promo_until == datetime(2026, 7, 30, 23, 59, 59)

        # Дата с таймзоной нормализуется к naive UTC
        s = Settings(legacy_promo_until="2026-07-31T00:00:00+03:00", **base)
        assert s.legacy_promo_until == datetime(2026, 7, 30, 21, 0, 0)
