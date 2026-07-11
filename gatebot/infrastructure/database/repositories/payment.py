from datetime import datetime, timedelta

from sqlalchemy import func, select, update

from core.interfaces.repositories.payment import PaymentRepository
from core.utils import utcnow
from infrastructure.database.models import Payment
from infrastructure.database.repositories.base import BaseRepository


class SQLPaymentRepository(BaseRepository, PaymentRepository):
    async def create(self, payment: Payment) -> Payment:
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_order_id(self, order_id: int) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.id == order_id)
        )
        return result.scalar_one_or_none()

    async def has_success_before(self, user_id: int, cutoff: datetime) -> bool:
        result = await self.session.execute(
            select(
                select(Payment.id)
                .where(
                    Payment.user_id == user_id,
                    Payment.status == "success",
                    Payment.created_at < cutoff,
                )
                .exists()
            )
        )
        return bool(result.scalar_one())

    async def get_latest_pending_by_user_id(self, user_id: int) -> Payment | None:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.user_id == user_id, Payment.status == "pending")
            .order_by(Payment.created_at.desc(), Payment.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(self, payment: Payment) -> None:
        await self.session.merge(payment)

    async def count_by_status(self, status: str) -> int:
        result = await self.session.execute(
            select(func.count(Payment.id)).where(Payment.status == status)
        )
        return int(result.scalar_one() or 0)

    async def sum_revenue(self, days_back: int | None = None) -> int:
        stmt = select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == "success"
        )
        if days_back is not None:
            since = utcnow() - timedelta(days=days_back)
            stmt = stmt.where(Payment.created_at >= since)
        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def expire_stale_pending(self, ttl_hours: int) -> int:
        cutoff = utcnow() - timedelta(hours=ttl_hours)
        stmt = (
            update(Payment)
            .where(Payment.status == "pending", Payment.created_at < cutoff)
            .values(status="expired")
        )
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)
