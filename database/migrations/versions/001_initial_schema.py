"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from app.database.base import UUIDType

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create products table
    op.create_table(
        'products',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('product_url', sa.String(length=2048), nullable=False),
        sa.Column('product_title', sa.String(length=512), nullable=False),
        sa.Column('platform', sa.String(length=64), nullable=False, server_default='Daraz'),
        sa.Column('category', sa.String(length=128), nullable=True),
        sa.Column('overall_rating', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_product_url'), 'products', ['product_url'], unique=True)

    # 2. Create analyses table
    op.create_table(
        'analyses',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('public_id', sa.String(length=64), nullable=False),
        sa.Column('product_id', UUIDType(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='completed'),
        sa.Column('execution_duration_ms', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('quality_risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('delivery_risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('trust_risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('business_risk_index', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('business_risk_level', sa.String(length=32), nullable=False),
        sa.Column('total_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_positive_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_negative_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_neutral_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('aspect_statistics', sa.JSON(), nullable=True),
        sa.Column('confidence_statistics', sa.JSON(), nullable=True),
        sa.Column('risk_breakdown', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analyses_public_id'), 'analyses', ['public_id'], unique=True)
    op.create_index(op.f('ix_analyses_product_id'), 'analyses', ['product_id'], unique=False)
    op.create_index(op.f('ix_analyses_business_risk_index'), 'analyses', ['business_risk_index'], unique=False)
    op.create_index(op.f('ix_analyses_business_risk_level'), 'analyses', ['business_risk_level'], unique=False)

    # 3. Create reviews table
    op.create_table(
        'reviews',
        sa.Column('id', UUIDType(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('analysis_id', UUIDType(), nullable=False),
        sa.Column('review_text', sa.Text(), nullable=False),
        sa.Column('sentiment', sa.String(length=32), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('aspects', sa.JSON(), nullable=True),
        sa.Column('language', sa.String(length=32), nullable=True),
        sa.Column('preprocessing_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reviews_analysis_id'), 'reviews', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_reviews_sentiment'), 'reviews', ['sentiment'], unique=False)


def downgrade() -> None:
    op.drop_table('reviews')
    op.drop_table('analyses')
    op.drop_table('products')
