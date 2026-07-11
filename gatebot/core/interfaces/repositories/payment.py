from abc import ABC, abstractmethod
from datetime import datetime

from infrastructure.database.models import Payment


class PaymentRepository(ABC):
    @abstractmethod
    async def create(self, payment: Payment) -> Payment: ...

    @abstractmethod
    async def get_by_order_id(self, order_id: int) -> Payment | None: ...

    @abstractmethod
    async def has_success_before(self, user_id: int, cutoff: datetime) -> bool: ...

    @abstractmethod
    async def get_latest_pending_by_user_id(self, user_id: int) -> Payment | None: ...

    @abstractmethod
    async def update(self, payment: Payment) -> None: ...

    @abstractmethod
    async def count_by_status(self, status: str) -> int: ...

    @abstractmethod
    async def sum_revenue(self, days_back: int | None = None) -> int: ...

    @abstractmethod
    async def expire_stale_pending(self, ttl_hours: int) -> int: ...
