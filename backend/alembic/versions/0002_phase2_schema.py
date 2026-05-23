"""Phase 2: tasks.completed_at, product_partner_links columns, rfq_partner_candidates columns

Revision ID: 0002_phase2_schema
Revises: 0001_initial
Create Date: 2026-05-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.migrations.schema_util import column_exists

revision: str = "0002_phase2_schema"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if not column_exists("tasks", "completed_at"):
        op.add_column("tasks", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))

    if not column_exists("product_partner_links", "capability_level"):
        op.add_column(
            "product_partner_links",
            sa.Column("capability_level", sa.String(length=64), nullable=True),
        )
    if not column_exists("product_partner_links", "partner_moq"):
        op.add_column("product_partner_links", sa.Column("partner_moq", sa.Integer(), nullable=True))
    if not column_exists("product_partner_links", "lead_time_days"):
        op.add_column("product_partner_links", sa.Column("lead_time_days", sa.Integer(), nullable=True))
    if not column_exists("product_partner_links", "partner_price_range"):
        op.add_column(
            "product_partner_links",
            sa.Column("partner_price_range", sa.String(length=255), nullable=True),
        )
    if not column_exists("product_partner_links", "sample_available"):
        op.add_column("product_partner_links", sa.Column("sample_available", sa.Boolean(), nullable=True))
    if not column_exists("product_partner_links", "certification_status"):
        op.add_column(
            "product_partner_links",
            sa.Column("certification_status", sa.String(length=255), nullable=True),
        )

    if not column_exists("rfq_partner_candidates", "partner_status"):
        op.add_column(
            "rfq_partner_candidates",
            sa.Column("partner_status", sa.String(length=64), nullable=True),
        )
    if not column_exists("rfq_partner_candidates", "quote_requested_at"):
        op.add_column(
            "rfq_partner_candidates",
            sa.Column("quote_requested_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not column_exists("rfq_partner_candidates", "quote_received_at"):
        op.add_column(
            "rfq_partner_candidates",
            sa.Column("quote_received_at", sa.DateTime(timezone=True), nullable=True),
        )
    if not column_exists("rfq_partner_candidates", "notes"):
        op.add_column("rfq_partner_candidates", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("rfq_partner_candidates", "notes")
    op.drop_column("rfq_partner_candidates", "quote_received_at")
    op.drop_column("rfq_partner_candidates", "quote_requested_at")
    op.drop_column("rfq_partner_candidates", "partner_status")

    op.drop_column("product_partner_links", "certification_status")
    op.drop_column("product_partner_links", "sample_available")
    op.drop_column("product_partner_links", "partner_price_range")
    op.drop_column("product_partner_links", "lead_time_days")
    op.drop_column("product_partner_links", "partner_moq")
    op.drop_column("product_partner_links", "capability_level")

    op.drop_column("tasks", "completed_at")
