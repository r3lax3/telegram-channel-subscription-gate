"""bigint payment id and expiring notice flag

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "expiring_notice_sent",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.alter_column(
        "payments",
        "id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "payments",
        "id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
    op.drop_column("users", "expiring_notice_sent")
