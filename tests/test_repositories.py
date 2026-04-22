import pytest
from datetime import datetime, timedelta

from infrastructure.database.models import User, Payment


@pytest.mark.asyncio
class TestUserRepository:
    async def test_get_or_create_new_user(self, uow):
        user = await uow.users.get_or_create(111111, "alice")
        await uow.commit()

        assert user.telegram_id == 111111
        assert user.username == "alice"
        assert user.id is not None

    async def test_get_or_create_existing_user(self, uow):
        user1 = await uow.users.get_or_create(222222, "bob")
        await uow.commit()

        user2 = await uow.users.get_or_create(222222, "bob_new")
        await uow.commit()

        assert user1.id == user2.id
        assert user2.username == "bob_new"

    async def test_get_by_telegram_id(self, uow):
        await uow.users.get_or_create(333333, "carol")
        await uow.commit()

        found = await uow.users.get_by_telegram_id(333333)
        assert found is not None
        assert found.telegram_id == 333333

    async def test_get_by_telegram_id_not_found(self, uow):
        found = await uow.users.get_by_telegram_id(999999)
        assert found is None

    async def test_get_all_users(self, uow):
        await uow.users.get_or_create(100001, "u1")
        await uow.users.get_or_create(100002, "u2")
        await uow.commit()

        users = await uow.users.get_all_users()
        assert len(users) == 2

    async def test_get_expiring_users(self, uow):
        user = await uow.users.get_or_create(400001, "expiring")
        user.is_active = True
        user.subscription_end_date = datetime.utcnow() + timedelta(days=2)
        await uow.users.update(user)
        await uow.commit()

        expiring = await uow.users.get_expiring_users(days_ahead=3)
        assert len(expiring) == 1
        assert expiring[0].telegram_id == 400001

    async def test_get_expiring_users_excludes_far_future(self, uow):
        user = await uow.users.get_or_create(400002, "safe")
        user.is_active = True
        user.subscription_end_date = datetime.utcnow() + timedelta(days=20)
        await uow.users.update(user)
        await uow.commit()

        expiring = await uow.users.get_expiring_users(days_ahead=3)
        assert len(expiring) == 0

    async def test_get_expired_users(self, uow):
        user = await uow.users.get_or_create(500001, "expired")
        user.is_active = True
        user.subscription_end_date = datetime.utcnow() - timedelta(hours=1)
        await uow.users.update(user)
        await uow.commit()

        expired = await uow.users.get_expired_users()
        assert len(expired) == 1
        assert expired[0].telegram_id == 500001

    async def test_get_expired_users_excludes_inactive(self, uow):
        user = await uow.users.get_or_create(500002, "inactive_expired")
        user.is_active = False
        user.subscription_end_date = datetime.utcnow() - timedelta(hours=1)
        await uow.users.update(user)
        await uow.commit()

        expired = await uow.users.get_expired_users()
        assert len(expired) == 0

    async def test_update_user(self, uow):
        user = await uow.users.get_or_create(600001, "update_me")
        user.username = "updated"
        await uow.users.update(user)
        await uow.commit()

        found = await uow.users.get_by_telegram_id(600001)
        assert found.username == "updated"


@pytest.mark.asyncio
class TestPaymentRepository:
    async def test_create_payment(self, uow):
        user = await uow.users.get_or_create(700001, "payer")
        await uow.commit()

        payment = Payment(
            id=1000000001,
            user_id=user.id,
            amount=1234,
            status="pending",
        )
        created = await uow.payments.create(payment)
        await uow.commit()

        assert created.id == 1000000001
        assert created.amount == 1234

    async def test_get_by_order_id(self, uow):
        user = await uow.users.get_or_create(700002, "payer2")
        await uow.commit()

        payment = Payment(
            id=1000000002,
            user_id=user.id,
            amount=999,
            status="pending",
        )
        await uow.payments.create(payment)
        await uow.commit()

        found = await uow.payments.get_by_order_id(1000000002)
        assert found is not None
        assert found.amount == 999

    async def test_get_by_order_id_not_found(self, uow):
        found = await uow.payments.get_by_order_id(9999999999)
        assert found is None

    async def test_update_payment(self, uow):
        user = await uow.users.get_or_create(700003, "payer3")
        await uow.commit()

        payment = Payment(
            id=1000000003,
            user_id=user.id,
            amount=500,
            status="pending",
        )
        await uow.payments.create(payment)
        await uow.commit()

        payment.status = "success"
        await uow.payments.update(payment)
        await uow.commit()

        found = await uow.payments.get_by_order_id(1000000003)
        assert found.status == "success"
