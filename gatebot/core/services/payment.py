import logging
import secrets

from core.config.settings import Settings
from core.interfaces.repositories.uow import UnitOfWork
from infrastructure.database.models import Payment

logger = logging.getLogger(__name__)

_MAX_ORDER_ID_RETRIES = 5


class PaymentService:
    def __init__(self, uow: UnitOfWork, settings: Settings) -> None:
        self.uow = uow
        self.settings = settings

    async def create_payment_link(
        self,
        telegram_id: int,
        username: str | None,
        amount: int,
        days: int,
        product_name: str | None = None,
    ) -> tuple[int, str]:
        from sqlalchemy.exc import IntegrityError
        from infrastructure.prodamus.client import ProdamusClient

        user = await self.uow.users.get_or_create(telegram_id, username)

        order_id: int | None = None
        for _ in range(_MAX_ORDER_ID_RETRIES):
            candidate = secrets.randbits(62)
            payment = Payment(
                id=candidate,
                user_id=user.id,
                amount=amount,
                days=days,
                status="pending",
            )
            try:
                await self.uow.payments.create(payment)
                order_id = candidate
                break
            except IntegrityError:
                await self.uow.rollback()
                continue
        if order_id is None:
            raise RuntimeError("Could not allocate unique order_id after retries")

        await self.uow.commit()

        client = ProdamusClient(self.settings)
        link = await client.create_payment_link(
            order_id=order_id,
            amount=amount,
            customer_extra=telegram_id,
            product_name=product_name,
        )
        logger.info("Payment link created for user %s, order %s", telegram_id, order_id)
        return order_id, link

    async def process_webhook(self, data: dict) -> Payment | None:
        payment = await self._find_pending_payment(data)
        if payment is None:
            return None

        payment.status = "success"
        await self.uow.payments.update(payment)
        await self.uow.commit()
        logger.info(
            "Payment processed: id=%s, user_id=%s", payment.id, payment.user_id
        )
        return payment

    async def _find_pending_payment(self, data: dict) -> Payment | None:
        order_id_raw = data.get("order_id")
        customer_extra_raw = data.get("customer_extra")

        payment: Payment | None = None
        if order_id_raw:
            try:
                payment = await self.uow.payments.get_by_order_id(int(order_id_raw))
            except (TypeError, ValueError):
                logger.warning("Webhook: invalid order_id=%r", order_id_raw)

        # Prodamus `order_num` is their internal counter and has no relation to
        # our Payment.id. When our `order_id` is missing from the webhook, fall
        # back to `customer_extra` (telegram_id) to locate the user's pending
        # payment.
        if payment is None and customer_extra_raw:
            try:
                telegram_id = int(customer_extra_raw)
            except (TypeError, ValueError):
                telegram_id = 0
            if telegram_id:
                user = await self.uow.users.get_by_telegram_id(telegram_id)
                if user is not None:
                    payment = await self.uow.payments.get_latest_pending_by_user_id(
                        user.id
                    )

        if payment is None:
            logger.warning(
                "Webhook ignored: no matching payment (order_id=%s, customer_extra=%s)",
                order_id_raw, customer_extra_raw,
            )
            return None

        if payment.status == "success":
            logger.warning(
                "Webhook ignored: payment id=%s already processed", payment.id
            )
            return None

        return payment
