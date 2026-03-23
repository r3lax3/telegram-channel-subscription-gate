from sqlalchemy.ext.asyncio import AsyncSession


class SQLUnitOfWork(BaseUnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self.user = 
    ...
