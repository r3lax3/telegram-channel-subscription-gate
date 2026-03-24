import time
import logging

from core.config.settings import Settings
from core.interfaces.repositories.uow import UnitOfWork
from infrastructure.database.models import Payment

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, uow: UnitOfWork, settings: Settings) -> None:
        self.uow = uow
        self.settings = settings

    async def create_payment_link(self, telegram_id: int, username: str | None) -> str:
        from infrastructure.prodamus.client import ProdamusClient

        user = await self.uow.users.get_or_create(telegram_id, username)
        order_id = f"sub_{telegram_id}_{int(time.time())}"
        payment = Payment(
            user_id=user.id,
            amount=self.settings.subscription_price,
            status="pending",
            prodamus_order_id=order_id,
        )
        await self.uow.payments.create(payment)
        await self.uow.commit()

        client = ProdamusClient(self.settings)
        link = await client.create_payment_link(
            order_id=order_id,
            amount=self.settings.subscription_price,
            customer_extra=str(telegram_id),
        )
        return link

    async def process_webhook(self, data: dict) -> bool:
        order_id = data.get("order_id") or data.get("order_num")
        if not order_id:
            return False

        payment = await self.uow.payments.get_by_order_id(str(order_id))
        if not payment or payment.status == "success":
            return False

        payment.status = "success"
        await self.uow.payments.update(payment)
        await self.uow.commit()
        return True
