from abc import ABC, abstractmethod

from infrastructure.database.models import Payment


class PaymentRepository(ABC):
    @abstractmethod
    async def create(self, payment: Payment) -> Payment: ...

    @abstractmethod
    async def get_by_order_id(self, order_id: str) -> Payment | None: ...

    @abstractmethod
    async def update(self, payment: Payment) -> None: ...
