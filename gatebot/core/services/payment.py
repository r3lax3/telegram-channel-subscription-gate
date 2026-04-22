import json
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
        order_id = int(time.time())
        payment = Payment(
            id=order_id,
            user_id=user.id,
            amount=self.settings.subscription_price,
            status="pending",
        )
        await self.uow.payments.create(payment)
        await self.uow.commit()

        client = ProdamusClient(self.settings)
        link = await client.create_payment_link(
            order_id=order_id,
            amount=self.settings.subscription_price,
            customer_extra=telegram_id,
        )
        logger.info("Payment link created for user %s, order %s", telegram_id, order_id)
        return link

    async def process_webhook(self, data: dict) -> bool:
        json.dump(data, open("./data.json", "w"))
        order_id = data.get("order_id") or data.get("order_num")
        if not order_id:
            logger.warning("Webhook ignored: missing order_id")
            return False

        payment = await self.uow.payments.get_by_order_id(int(order_id))
        if not payment or payment.status == "success":
            logger.warning("Webhook ignored: order_id=%s not found or already processed", order_id)
            return False

        payment.status = "success"
        await self.uow.payments.update(payment)
        await self.uow.commit()
        logger.info("Payment processed for order %s", order_id)
        return True
