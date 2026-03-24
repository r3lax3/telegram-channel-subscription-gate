import sys
import os

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Add gatebot to the path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "gatebot"))

from infrastructure.database.models import Base, User, Payment
from infrastructure.database.uow import SQLUnitOfWork
from core.config.settings import Settings


@pytest.fixture
def settings():
    return Settings(
        debug=True,
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379",
        bot_token="test:token",
        owner_ids=[12345678],
        support_link="https://t.me/test",
        channel_id=-100123456789,
        subscription_price=1234,
        subscription_days=30,
        prodamus_api_key="test_key",
        prodamus_domain="test.payform.ru",
        prodamus_secret_key="test_secret",
        webhook_host="https://test.com",
        webhook_port=8080,
    )


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def uow(session):
    return SQLUnitOfWork(session)


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    invite_link = MagicMock()
    invite_link.invite_link = "https://t.me/+test_invite_link"
    bot.create_chat_invite_link.return_value = invite_link
    bot.ban_chat_member.return_value = True
    bot.unban_chat_member.return_value = True
    bot.send_message.return_value = True
    return bot
