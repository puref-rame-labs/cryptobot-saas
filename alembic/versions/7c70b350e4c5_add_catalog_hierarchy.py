"""add catalog hierarchy

Revision ID: 7c70b350e4c5
Revises: 6b54606645a0
Create Date: 2026-07-08 20:30:23.210410

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7c70b350e4c5'
down_revision: Union[str, Sequence[str], None] = '6b54606645a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'subcategories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'product_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('subcategory_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['subcategory_id'], ['subcategories.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'brands',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('product_group_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['product_group_id'], ['product_groups.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('brand_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_products_brand_id', 'brands', ['brand_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_constraint('fk_products_brand_id', type_='foreignkey')
        batch_op.drop_column('brand_id')

    op.drop_table('brands')
    op.drop_table('product_groups')
    op.drop_table('subcategories')
    op.drop_table('categories')
