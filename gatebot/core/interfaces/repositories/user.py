from abc import ABC, abstractmethod

from infrastructure.database.models import User


class UserRepository(ABC):
    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> User | None: ...

    @abstractmethod
    async def get_or_create(self, telegram_id: int, username: str | None) -> User: ...

    @abstractmethod
    async def get_all_users(self) -> list[User]: ...

    @abstractmethod
    async def get_expiring_users(self, days_ahead: int) -> list[User]: ...

    @abstractmethod
    async def get_expired_users(self) -> list[User]: ...

    @abstractmethod
    async def update(self, user: User) -> None: ...
