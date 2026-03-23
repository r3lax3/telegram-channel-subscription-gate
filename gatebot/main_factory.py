from dishka import (
    AsyncContainer,
    make_async_container,
    STRICT_VALIDATION,
)
from typing import AsyncIterable

from dishka import Provider, Scope, provide, AsyncContainer
from dishka.integrations.aiogram import setup_dishka

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.base import BaseStorage, DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage

from aiogram_dialog import BgManagerFactory

from redis.asyncio import Redis

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config.settings import Settings
from core.interfaces.uow import UnitOfWork
from infrastructure.database.uow import SQLUnitOfWork
from tgbot.handlers import setup_handlers


class ConfigProvider(Provider):
    scope = Scope.APP

    @provide
    def get_settings(self) -> Settings:
        return Settings()  # type: ignore


class DatabaseProvider(Provider):
    scope = Scope.APP

    @provide
    def create_engine(self, settings: Settings) -> AsyncEngine:
        return create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )

    @provide
    def get_session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            engine,
            expire_on_commit=False,
            autoflush=False,
        )


class SessionProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def create_session(
        self,
        session_factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with session_factory() as session:
            yield session


class UOWProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def create_uow(
        self,
        session: AsyncSession
    ) -> UnitOfWork:
        return SQLUnitOfWork(session)


class DispatcherProvider(Provider):
    scope = Scope.APP

    @provide
    def create_storage(self, redis: Redis) -> BaseStorage:
        return RedisStorage(
            redis=redis,
            key_builder=DefaultKeyBuilder(with_destiny=True)
        )

    @provide
    def create_dispatcher(
        self,
        dishka: AsyncContainer,
        storage: BaseStorage,
    ) -> Dispatcher:
        dp = Dispatcher(storage=storage)

        setup_dishka(container=dishka, router=dp, auto_inject=True)

        bg_manager_factory = setup_handlers(dp)
        dp["bg_manager_factory"] = bg_manager_factory  # save it to dp so i can acces to it

        return dp


class RedisProvider(Provider):
    scope = Scope.APP

    @provide
    def create_redis(
        self,
        settings: Settings
    ) -> Redis:
        return Redis.from_url(settings.redis_url)


class BotProvider(Provider):
    scope = Scope.APP

    @provide
    def create_bot(self, settings: Settings) -> Bot:
        return Bot(token=settings.bot_token)


class BgManagerProvider(Provider):
    scope = Scope.APP

    @provide
    def create_bg_manager_factory(
        self,
        dp: Dispatcher,
    ) -> BgManagerFactory:
        return dp["bg_manager_factory"]


def get_all_dishka_providers() -> list[Provider]:
    return [
        ConfigProvider(),
        DatabaseProvider(),
        SessionProvider(),
        UOWProvider(),
        DispatcherProvider(),
        RedisProvider(),
        BotProvider()
    ]


def create_dishka() -> AsyncContainer:
    container = make_async_container(
        *get_all_dishka_providers(),
        validation_settings=STRICT_VALIDATION
    )
    return container
