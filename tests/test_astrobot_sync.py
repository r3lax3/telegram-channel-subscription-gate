import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from core.services.subscription import SubscriptionService
from infrastructure.astrobot.client import AstrobotClient


def _settings_with_sync(settings, enabled=True, url="http://astrobot/sync", secret="shared"):
    settings.astrobot_sync_enabled = enabled
    settings.astrobot_sync_url = url
    settings.astrobot_sync_secret = secret
    return settings


class TestAstrobotClient:
    @pytest.mark.asyncio
    async def test_notify_is_signed_and_payload_is_iso(self, settings):
        settings = _settings_with_sync(settings)
        client = AstrobotClient(settings)
        end_date = datetime(2026, 2, 28, 12, 0, 0)

        captured = {}

        class _Resp:
            status = 200
            async def text(self):
                return ""
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                return False

        class _Session:
            def __init__(self, *a, **kw):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *a):
                return False
            def post(self, url, data=None, headers=None):
                captured["url"] = url
                captured["data"] = data
                captured["headers"] = headers
                return _Resp()

        with patch("infrastructure.astrobot.client.aiohttp.ClientSession", _Session):
            await client.notify(111, end_date)

        assert captured["url"] == "http://astrobot/sync"
        payload = json.loads(captured["data"])
        assert payload == {
            "user_id": 111,
            "subscription_end_date": "2026-02-28T12:00:00",
        }
        expected_sig = hmac.new(
            b"shared", captured["data"], hashlib.sha256
        ).hexdigest()
        assert captured["headers"]["X-Signature"] == expected_sig

    @pytest.mark.asyncio
    async def test_notify_swallows_exceptions(self, settings):
        settings = _settings_with_sync(settings)
        client = AstrobotClient(settings)

        class _Boom:
            def __init__(self, *a, **kw):
                pass
            async def __aenter__(self):
                raise RuntimeError("network down")
            async def __aexit__(self, *a):
                return False

        with patch("infrastructure.astrobot.client.aiohttp.ClientSession", _Boom):
            # must not raise
            await client.notify(111, datetime.utcnow())

    @pytest.mark.asyncio
    async def test_notify_noop_when_url_or_secret_missing(self, settings):
        settings = _settings_with_sync(settings, url="", secret="x")
        client = AstrobotClient(settings)
        with patch(
            "infrastructure.astrobot.client.aiohttp.ClientSession",
            side_effect=AssertionError("should not be called"),
        ):
            await client.notify(111, datetime.utcnow())


@pytest.mark.asyncio
class TestSubscriptionServiceSync:
    async def test_activate_calls_sync_when_enabled(
        self, uow, mock_bot, settings
    ):
        settings = _settings_with_sync(settings, enabled=True)
        service = SubscriptionService(uow, mock_bot, settings)
        with patch(
            "core.services.subscription.AstrobotClient"
        ) as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.notify = AsyncMock()
            await service.activate_subscription(333, "carol")
            mock_client.notify.assert_awaited_once()
            args = mock_client.notify.await_args.args
            assert args[0] == 333
            assert isinstance(args[1], datetime)

    async def test_activate_skips_sync_when_disabled(
        self, uow, mock_bot, settings
    ):
        settings = _settings_with_sync(settings, enabled=False)
        service = SubscriptionService(uow, mock_bot, settings)
        with patch(
            "core.services.subscription.AstrobotClient"
        ) as mock_client_cls:
            await service.activate_subscription(444, "dave")
            mock_client_cls.assert_not_called()

    async def test_set_subscription_end_syncs_when_active(
        self, uow, mock_bot, settings
    ):
        settings = _settings_with_sync(settings, enabled=True)
        user = await uow.users.get_or_create(555, "eve")
        await uow.users.update(user)
        await uow.commit()

        service = SubscriptionService(uow, mock_bot, settings)
        future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(
            days=60
        )
        with patch(
            "core.services.subscription.AstrobotClient"
        ) as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.notify = AsyncMock()
            await service.set_subscription_end(555, future)
            mock_client.notify.assert_awaited_once_with(555, future)

    async def test_set_subscription_end_skips_sync_when_past(
        self, uow, mock_bot, settings
    ):
        settings = _settings_with_sync(settings, enabled=True)
        user = await uow.users.get_or_create(666, "frank")
        await uow.users.update(user)
        await uow.commit()

        service = SubscriptionService(uow, mock_bot, settings)
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            days=1
        )
        with patch(
            "core.services.subscription.AstrobotClient"
        ) as mock_client_cls:
            await service.set_subscription_end(666, past)
            mock_client_cls.assert_not_called()
