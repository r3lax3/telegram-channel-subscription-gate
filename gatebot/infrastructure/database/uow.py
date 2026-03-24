from sqlalchemy.ext.asyncio import AsyncSession

from core.interfaces.repositories.uow import UnitOfWork
from infrastructure.database.repositories.user import SQLUserRepository
from infrastructure.database.repositories.payment import SQLPaymentRepository


class SQLUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = SQLUserRepository(session)
        self.payments = SQLPaymentRepository(session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
