"""add seller_name and image_url to products

Revision ID: 002_add_seller_and_image
Revises: 001_initial_schema
Create Date: 2026-07-28 18:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_seller_and_image'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.add_column('products', sa.Column('seller_name', sa.String(length=256), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('products', sa.Column('image_url', sa.String(length=2048), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_column('products', 'image_url')
    except Exception:
        pass

    try:
        op.drop_column('products', 'seller_name')
    except Exception:
        pass
