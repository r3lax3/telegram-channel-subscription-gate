import pytest
from datetime import datetime

from infrastructure.database.models import User, Payment


class TestUserModel:
    def test_create_user(self):
        user = User(telegram_id=123456, username="testuser")
        assert user.telegram_id == 123456
        assert user.username == "testuser"
        assert user.is_active is None  # default set at DB level
        assert user.subscription_end_date is None

    def test_user_repr(self):
        user = User(id=1, telegram_id=123456, is_active=True)
        assert "123456" in repr(user)


class TestPaymentModel:
    def test_create_payment(self):
        payment = Payment(
            user_id=1,
            amount=1234,
            status="pending",
            prodamus_order_id="sub_123_1000",
        )
        assert payment.amount == 1234
        assert payment.status == "pending"
        assert payment.prodamus_order_id == "sub_123_1000"

    def test_payment_repr(self):
        payment = Payment(id=1, user_id=1, status="success")
        assert "success" in repr(payment)
