from sqlalchemy import select

from core.interfaces.repositories.payment import PaymentRepository
from infrastructure.database.models import Payment
from infrastructure.database.repositories.base import BaseRepository


class SQLPaymentRepository(BaseRepository, PaymentRepository):
    async def create(self, payment: Payment) -> Payment:
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_order_id(self, order_id: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.id == order_id)
        )
        return result.scalar_one_or_none()

    async def update(self, payment: Payment) -> None:
        await self.session.merge(payment)
