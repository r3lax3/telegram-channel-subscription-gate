"""legacy pricing flag and payment days

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Дата отсечки: «старички» — те, кто впервые оплатил не позже этой даты (UTC)
# и чья подписка активна на момент миграции. Поменять перед деплоем, если
# заказчица назовёт другую дату.
LEGACY_CUTOFF_UTC = "2026-06-30 23:59:59"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "legacy_pricing",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column(
        "payments",
        sa.Column("days", sa.Integer(), nullable=False, server_default="30"),
    )
    op.execute(
        f"""
        UPDATE users SET legacy_pricing = true
        WHERE is_active = true
          AND subscription_end_date IS NOT NULL
          AND subscription_end_date > timezone('utc', now())
          AND id IN (
              SELECT user_id FROM payments
              WHERE status = 'success' AND created_at <= '{LEGACY_CUTOFF_UTC}'
          )
        """
    )


def downgrade() -> None:
    op.drop_column("payments", "days")
    op.drop_column("users", "legacy_pricing")
