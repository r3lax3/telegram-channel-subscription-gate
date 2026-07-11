from datetime import datetime

import pytest

from core.config.settings import Settings


class TestSettings:
    def test_settings_from_kwargs(self, settings):
        assert settings.debug is True
        assert settings.bot_token == "test:token"
        assert settings.owner_ids == [12345678]
        assert settings.channel_id == -100123456789
        assert settings.subscription_price == 1234
        assert settings.subscription_days == 30

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
        assert s.subscription_price == 1234
        assert s.subscription_days == 30
        assert s.webhook_port == 8080
        assert s.early_bird_price == 1500
        assert s.early_bird_deadline is None

    def test_early_bird_deadline_normalized_to_naive_utc(self):
        s = Settings(
            database_url="sqlite:///:memory:",
            redis_url="redis://localhost:6379",
            bot_token="test:token",
            owner_ids=[1],
            support_link="https://t.me/test",
            channel_id=-100123,
            early_bird_deadline="2026-08-01T00:00:00+03:00",
            _env_file=None,
        )
        assert s.early_bird_deadline == datetime(2026, 7, 31, 21, 0, 0)
        assert s.early_bird_deadline.tzinfo is None

    def test_early_bird_deadline_naive_kept_as_is(self):
        s = Settings(
            database_url="sqlite:///:memory:",
            redis_url="redis://localhost:6379",
            bot_token="test:token",
            owner_ids=[1],
            support_link="https://t.me/test",
            channel_id=-100123,
            early_bird_deadline="2026-08-01T00:00:00",
            _env_file=None,
        )
        assert s.early_bird_deadline == datetime(2026, 8, 1, 0, 0, 0)
