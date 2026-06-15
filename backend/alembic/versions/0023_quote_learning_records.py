"""add quote learning records

Revision ID: 0023_quote_learning_records
Revises: 0022_sales_opportunities
Create Date: 2026-06-15
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0023_quote_learning_records"
down_revision = "0022_sales_opportunities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quote_learning_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome_status", sa.String(length=32), nullable=False),
        sa.Column("customer_feedback", sa.Text(), nullable=True),
        sa.Column("customer_objection", sa.Text(), nullable=True),
        sa.Column("competitor_signal", sa.Text(), nullable=True),
        sa.Column("won_reason", sa.Text(), nullable=True),
        sa.Column("lost_reason", sa.Text(), nullable=True),
        sa.Column("price_feedback", sa.Text(), nullable=True),
        sa.Column("delivery_feedback", sa.Text(), nullable=True),
        sa.Column("product_feedback", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("product_dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("next_action", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(length=256), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("affects_product_intelligence", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("affects_market_response", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("affects_opportunity", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("internal_only", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quote_version_id"], ["quote_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_learning_records_quote_id", "quote_learning_records", ["quote_id"])
    op.create_index("ix_quote_learning_records_outcome_status", "quote_learning_records", ["outcome_status"])


def downgrade() -> None:
    op.drop_index("ix_quote_learning_records_outcome_status", table_name="quote_learning_records")
    op.drop_index("ix_quote_learning_records_quote_id", table_name="quote_learning_records")
    op.drop_table("quote_learning_records")
