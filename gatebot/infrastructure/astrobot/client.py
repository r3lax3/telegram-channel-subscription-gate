import hashlib
import hmac
import json
import logging
from datetime import datetime

import aiohttp

from core.config.settings import Settings

logger = logging.getLogger(__name__)

_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"
_REQUEST_TIMEOUT_SECONDS = 5


class AstrobotClient:
    """
    Best-effort notifier that tells astrobot a subscription was just
    activated/extended in gatebot. Astrobot decides whether to extend
    its own subscription (never shortens).

    All errors are swallowed: a failed sync must not break gatebot's
    payment flow.
    """

    def __init__(self, settings: Settings) -> None:
        self.url = settings.astrobot_sync_url
        self.secret = settings.astrobot_sync_secret

    async def notify(
        self,
        telegram_id: int,
        subscription_end_date_utc: datetime,
    ) -> None:
        if not self.url or not self.secret:
            logger.warning(
                "Astrobot sync skipped: URL or secret is empty"
            )
            return

        payload = {
            "user_id": telegram_id,
            "subscription_end_date": subscription_end_date_utc.strftime(
                _ISO_FORMAT
            ),
        }
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(
            self.secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature,
        }
        timeout = aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT_SECONDS)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.url, data=body, headers=headers
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.warning(
                            "Astrobot sync: non-200 response %s for user %s: %s",
                            resp.status, telegram_id, text[:200],
                        )
                        return
            logger.info(
                "Astrobot sync ok for user %s until %s",
                telegram_id, payload["subscription_end_date"],
            )
        except Exception:
            logger.exception(
                "Astrobot sync failed for user %s", telegram_id
            )
