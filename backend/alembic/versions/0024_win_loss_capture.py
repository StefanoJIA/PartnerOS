"""add structured win loss capture fields

Revision ID: 0024_win_loss_capture
Revises: 0023_quote_learning_records
Create Date: 2026-06-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0024_win_loss_capture"
down_revision = "0023_quote_learning_records"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return index_name in {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not column_exists("quote_learning_records", "reason_category"):
        op.add_column("quote_learning_records", sa.Column("reason_category", sa.String(length=64), nullable=True))
    if not column_exists("quote_learning_records", "customer_decision_factors"):
        op.add_column(
            "quote_learning_records",
            sa.Column("customer_decision_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    if not column_exists("quote_learning_records", "product_factors"):
        op.add_column("quote_learning_records", sa.Column("product_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    if not column_exists("quote_learning_records", "partner_factors"):
        op.add_column("quote_learning_records", sa.Column("partner_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    if not column_exists("quote_learning_records", "outcome_source_type"):
        op.add_column(
            "quote_learning_records",
            sa.Column("outcome_source_type", sa.String(length=32), nullable=False, server_default="quote"),
        )
    if not column_exists("quote_learning_records", "outcome_source_id"):
        op.add_column("quote_learning_records", sa.Column("outcome_source_id", postgresql.UUID(as_uuid=True), nullable=True))
    if not index_exists("quote_learning_records", "ix_quote_learning_records_reason_category"):
        op.create_index("ix_quote_learning_records_reason_category", "quote_learning_records", ["reason_category"])
    if not index_exists("quote_learning_records", "ix_quote_learning_records_outcome_source_type"):
        op.create_index("ix_quote_learning_records_outcome_source_type", "quote_learning_records", ["outcome_source_type"])

    if not column_exists("sales_opportunities", "outcome_status"):
        op.add_column("sales_opportunities", sa.Column("outcome_status", sa.String(length=32), nullable=True))
    if not column_exists("sales_opportunities", "outcome_reason_category"):
        op.add_column("sales_opportunities", sa.Column("outcome_reason_category", sa.String(length=64), nullable=True))
    if not column_exists("sales_opportunities", "customer_decision_factors"):
        op.add_column(
            "sales_opportunities",
            sa.Column("customer_decision_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    if not column_exists("sales_opportunities", "product_factors"):
        op.add_column("sales_opportunities", sa.Column("product_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    if not column_exists("sales_opportunities", "partner_factors"):
        op.add_column("sales_opportunities", sa.Column("partner_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    if not column_exists("sales_opportunities", "outcome_recorded_at"):
        op.add_column("sales_opportunities", sa.Column("outcome_recorded_at", sa.DateTime(timezone=True), nullable=True))
    if not index_exists("sales_opportunities", "ix_sales_opportunities_outcome_status"):
        op.create_index("ix_sales_opportunities_outcome_status", "sales_opportunities", ["outcome_status"])
    if not index_exists("sales_opportunities", "ix_sales_opportunities_outcome_reason_category"):
        op.create_index("ix_sales_opportunities_outcome_reason_category", "sales_opportunities", ["outcome_reason_category"])


def downgrade() -> None:
    op.drop_index("ix_sales_opportunities_outcome_reason_category", table_name="sales_opportunities")
    op.drop_index("ix_sales_opportunities_outcome_status", table_name="sales_opportunities")
    op.drop_column("sales_opportunities", "outcome_recorded_at")
    op.drop_column("sales_opportunities", "partner_factors")
    op.drop_column("sales_opportunities", "product_factors")
    op.drop_column("sales_opportunities", "customer_decision_factors")
    op.drop_column("sales_opportunities", "outcome_reason_category")
    op.drop_column("sales_opportunities", "outcome_status")

    op.drop_index("ix_quote_learning_records_outcome_source_type", table_name="quote_learning_records")
    op.drop_index("ix_quote_learning_records_reason_category", table_name="quote_learning_records")
    op.drop_column("quote_learning_records", "outcome_source_id")
    op.drop_column("quote_learning_records", "outcome_source_type")
    op.drop_column("quote_learning_records", "partner_factors")
    op.drop_column("quote_learning_records", "product_factors")
    op.drop_column("quote_learning_records", "customer_decision_factors")
    op.drop_column("quote_learning_records", "reason_category")
