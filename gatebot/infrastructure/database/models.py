from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_end_date: Mapped[datetime | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    payments: Mapped[list["Payment"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, tg={self.telegram_id}, active={self.is_active})>"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(20), default="pending")
    payment_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, user={self.user_id}, status={self.status})>"
