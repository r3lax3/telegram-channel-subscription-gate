from abc import ABC, abstractmethod

from infrastructure.database.models import Payment


class PaymentRepository(ABC):
    @abstractmethod
    async def create(self, payment: Payment) -> Payment: ...

    @abstractmethod
    async def get_by_order_id(self, order_id: int) -> Payment | None: ...

    @abstractmethod
    async def get_latest_pending_by_user_id(self, user_id: int) -> Payment | None: ...

    @abstractmethod
    async def update(self, payment: Payment) -> None: ...
