import asyncio
import logging
from pathlib import Path

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from core.config.settings import Settings

logger = logging.getLogger(__name__)


class InviteService:
    def __init__(self, bot: Bot, settings: Settings) -> None:
        self.bot = bot
        self.channel_id = settings.channel_id
        self.path = Path(settings.invite_link_file)
        self.name = settings.invite_link_name
        self._link: str | None = None
        self._lock = asyncio.Lock()

    async def ensure_link(self) -> str:
        if self._link:
            return self._link
        async with self._lock:
            if self._link:
                return self._link
            stored = self._load()
            if stored and await self._is_alive(stored):
                logger.info("Reusing stored channel invite link")
                self._link = stored
                return stored
            self._link = await self._create()
            self._save(self._link)
            logger.info("Created new channel invite link")
            return self._link

    async def _create(self) -> str:
        result = await self.bot.create_chat_invite_link(
            chat_id=self.channel_id,
            creates_join_request=True,
            name=self.name,
        )
        return result.invite_link

    async def _is_alive(self, link: str) -> bool:
        try:
            await self.bot.edit_chat_invite_link(
                chat_id=self.channel_id,
                invite_link=link,
                creates_join_request=True,
                name=self.name,
            )
            return True
        except TelegramBadRequest as e:
            logger.warning("Stored invite link is not alive: %s", e)
            return False

    def _load(self) -> str | None:
        try:
            value = self.path.read_text(encoding="utf-8").strip()
            return value or None
        except FileNotFoundError:
            return None

    def _save(self, link: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(link, encoding="utf-8")
