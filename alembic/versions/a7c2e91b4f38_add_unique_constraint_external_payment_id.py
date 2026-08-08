"""add unique constraint to invoices.external_payment_id

Revision ID: a7c2e91b4f38
Revises: f3a1c9d47b62
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7c2e91b4f38'
down_revision: Union[str, Sequence[str], None] = 'f3a1c9d47b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # domain_model.md Invoice Invariants: "external_payment_id must be
    # unique." Was never enforced at the DB level - get_by_external_payment_id()
    # relied on this holding true without any constraint backing it.
    # Confirmed no existing duplicate data before adding this (see
    # known_issues.md item 3).
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_invoices_external_payment_id',
            ['external_payment_id'],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.drop_constraint(
            'uq_invoices_external_payment_id',
            type_='unique',
        )
