"""make payment_event invoice_id nullable

Revision ID: f3a1c9d47b62
Revises: cadc800cbb81
Create Date: 2026-08-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3a1c9d47b62'
down_revision: Union[str, Sequence[str], None] = 'cadc800cbb81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # webhook_idempotency.md: "EVERY webhook event must be stored.
    # Even invalid ones." A webhook for an unknown external_payment_id
    # has no invoice to attach to, so invoice_id must be nullable to
    # allow persisting the event anyway.
    with op.batch_alter_table('payment_events', schema=None) as batch_op:
        batch_op.alter_column(
            'invoice_id',
            existing_type=sa.Integer(),
            nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('payment_events', schema=None) as batch_op:
        batch_op.alter_column(
            'invoice_id',
            existing_type=sa.Integer(),
            nullable=False,
        )
