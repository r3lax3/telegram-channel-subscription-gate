from datetime import datetime, timedelta

from sqlalchemy import func, select

from core.interfaces.repositories.user import UserRepository
from infrastructure.database.models import User
from infrastructure.database.repositories.base import BaseRepository


class SQLUserRepository(BaseRepository, UserRepository):
    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        normalized = username.lstrip("@")
        if not normalized:
            return None
        result = await self.session.execute(
            select(User).where(func.lower(User.username) == normalized.lower())
        )
        return result.scalars().first()

    async def get_or_create(self, telegram_id: int, username: str | None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = User(telegram_id=telegram_id, username=username)
            self.session.add(user)
            await self.session.flush()
        else:
            if username and user.username != username:
                user.username = username
        return user

    async def get_all_users(self) -> list[User]:
        result = await self.session.execute(select(User))
        return list(result.scalars().all())

    async def get_expiring_users(self, days_ahead: int) -> list[User]:
        now = datetime.utcnow()
        deadline = now + timedelta(days=days_ahead)
        result = await self.session.execute(
            select(User).where(
                User.is_active.is_(True),
                User.subscription_end_date.isnot(None),
                User.subscription_end_date > now,
                User.subscription_end_date <= deadline,
            )
        )
        return list(result.scalars().all())

    async def get_expired_users(self) -> list[User]:
        now = datetime.utcnow()
        result = await self.session.execute(
            select(User).where(
                User.is_active.is_(True),
                User.subscription_end_date.isnot(None),
                User.subscription_end_date <= now,
            )
        )
        return list(result.scalars().all())

    async def update(self, user: User) -> None:
        await self.session.merge(user)

    async def count_total(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return int(result.scalar_one() or 0)

    async def count_active_subscribers(self) -> int:
        now = datetime.utcnow()
        result = await self.session.execute(
            select(func.count(User.id)).where(
                User.is_active.is_(True),
                User.subscription_end_date.isnot(None),
                User.subscription_end_date > now,
            )
        )
        return int(result.scalar_one() or 0)

    async def count_expiring_within(self, days_ahead: int) -> int:
        now = datetime.utcnow()
        deadline = now + timedelta(days=days_ahead)
        result = await self.session.execute(
            select(func.count(User.id)).where(
                User.is_active.is_(True),
                User.subscription_end_date.isnot(None),
                User.subscription_end_date > now,
                User.subscription_end_date <= deadline,
            )
        )
        return int(result.scalar_one() or 0)
