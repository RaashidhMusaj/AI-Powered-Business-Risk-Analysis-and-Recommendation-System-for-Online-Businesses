"""add users table and tenant isolation user_id columns

Revision ID: 003_add_users_and_tenant_isolation
Revises: 002_add_seller_and_image
Create Date: 2026-07-29 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime, timezone
from app.database.base import UUIDType

# revision identifiers, used by Alembic.
revision: str = '003_add_users_and_tenant_isolation'
down_revision: Union[str, None] = '002_add_seller_and_image'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    # 1. Create users table
    try:
        op.create_table(
            'users',
            sa.Column('id', UUIDType(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('username', sa.String(length=64), nullable=False),
            sa.Column('hashed_password', sa.String(length=255), nullable=False),
            sa.Column('full_name', sa.String(length=128), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    except Exception:
        pass

    # 2. Insert default fallback user for existing data backfill
    conn = op.get_bind()
    now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn.execute(sa.text(f"""
            INSERT INTO users (id, created_at, updated_at, email, username, hashed_password, full_name, is_active)
            VALUES ('{DEFAULT_USER_ID}', '{now_iso}', '{now_iso}', 'system@local', 'system_admin', 'hashed_system', 'System Admin', true)
            ON CONFLICT (id) DO NOTHING
        """))
    except Exception:
        pass

    # 3. Add user_id column to products, analyses, reviews
    for table_name in ['products', 'analyses', 'reviews']:
        try:
            op.add_column(table_name, sa.Column('user_id', UUIDType(), nullable=True))
            conn.execute(sa.text(f"UPDATE {table_name} SET user_id = '{DEFAULT_USER_ID}' WHERE user_id IS NULL"))
            op.alter_column(table_name, 'user_id', nullable=False)
            op.create_index(f'ix_{table_name}_user_id', table_name, ['user_id'])
        except Exception:
            pass

    # 4. Create composite indexes
    try:
        op.create_index('idx_products_user_created', 'products', ['user_id', 'created_at'])
        op.create_index('idx_analyses_user_created', 'analyses', ['user_id', 'created_at'])
        op.create_index('idx_analyses_user_risk_level', 'analyses', ['user_id', 'business_risk_level'])
        op.create_index('idx_reviews_user_analysis', 'reviews', ['user_id', 'analysis_id'])
    except Exception:
        pass


def downgrade() -> None:
    for table_name in ['products', 'analyses', 'reviews']:
        try:
            op.drop_index(f'ix_{table_name}_user_id', table_name=table_name)
            op.drop_column(table_name, 'user_id')
        except Exception:
            pass

    try:
        op.drop_index(op.f('ix_users_username'), table_name='users')
        op.drop_index(op.f('ix_users_email'), table_name='users')
        op.drop_table('users')
    except Exception:
        pass
