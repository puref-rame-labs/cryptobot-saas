"""add referral program

Revision ID: b3f7a19c2d05
Revises: a7c2e91b4f38
Create Date: 2026-08-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f7a19c2d05'
down_revision: Union[str, Sequence[str], None] = 'a7c2e91b4f38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('referral_code', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('referred_by_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint('uq_users_referral_code', ['referral_code'])
        batch_op.create_foreign_key(
            'fk_users_referred_by_id_users',
            'users',
            ['referred_by_id'],
            ['id'],
        )

    op.create_table(
        'referral_accruals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('referrer_id', sa.Integer(), nullable=False),
        sa.Column('referred_user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(18, 8), nullable=False),
        sa.Column('currency', sa.String(length=16), nullable=False),
        sa.Column('percent', sa.Numeric(5, 2), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('paid_out_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id']),
        sa.ForeignKeyConstraint(['referrer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['referred_user_id'], ['users.id']),
        sa.UniqueConstraint('invoice_id', name='uq_referral_accruals_invoice_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('referral_accruals')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_referred_by_id_users', type_='foreignkey')
        batch_op.drop_constraint('uq_users_referral_code', type_='unique')
        batch_op.drop_column('referred_by_id')
        batch_op.drop_column('referral_code')
