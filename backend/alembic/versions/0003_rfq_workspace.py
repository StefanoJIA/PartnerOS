"""RFQ workspace: rfq_items + candidate enrichment + sample.rfq_id + order.lead_id

Revision ID: 0003_rfq_workspace
Revises: 0002_phase2_schema
Create Date: 2026-05-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.migrations.schema_util import column_exists, fk_exists

revision: str = "0003_rfq_workspace"
down_revision: str | None = "0002_phase2_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if not column_exists("rfq_items", "target_price"):
        op.add_column("rfq_items", sa.Column("target_price", sa.Numeric(18, 2), nullable=True))
    if not column_exists("rfq_items", "required_certifications"):
        op.add_column("rfq_items", sa.Column("required_certifications", sa.Text(), nullable=True))
    if not column_exists("rfq_items", "packaging_requirement"):
        op.add_column("rfq_items", sa.Column("packaging_requirement", sa.Text(), nullable=True))
    if not column_exists("rfq_items", "shipping_requirement"):
        op.add_column("rfq_items", sa.Column("shipping_requirement", sa.Text(), nullable=True))

    if not column_exists("rfq_partner_candidates", "is_preferred"):
        op.add_column(
            "rfq_partner_candidates",
            sa.Column("is_preferred", sa.Boolean(), nullable=False, server_default="false"),
        )
        op.alter_column("rfq_partner_candidates", "is_preferred", server_default=None)
    if not column_exists("rfq_partner_candidates", "capability_level"):
        op.add_column("rfq_partner_candidates", sa.Column("capability_level", sa.String(length=64), nullable=True))
    if not column_exists("rfq_partner_candidates", "partner_moq"):
        op.add_column("rfq_partner_candidates", sa.Column("partner_moq", sa.Integer(), nullable=True))
    if not column_exists("rfq_partner_candidates", "lead_time_days"):
        op.add_column("rfq_partner_candidates", sa.Column("lead_time_days", sa.Integer(), nullable=True))
    if not column_exists("rfq_partner_candidates", "partner_price_range"):
        op.add_column(
            "rfq_partner_candidates",
            sa.Column("partner_price_range", sa.String(length=255), nullable=True),
        )
    if not column_exists("rfq_partner_candidates", "sample_available"):
        op.add_column("rfq_partner_candidates", sa.Column("sample_available", sa.Boolean(), nullable=True))
    if not column_exists("rfq_partner_candidates", "certification_status"):
        op.add_column(
            "rfq_partner_candidates",
            sa.Column("certification_status", sa.String(length=255), nullable=True),
        )
    if not column_exists("rfq_partner_candidates", "product_fit"):
        op.add_column("rfq_partner_candidates", sa.Column("product_fit", sa.String(length=64), nullable=True))

    if not column_exists("samples", "rfq_id"):
        op.add_column("samples", sa.Column("rfq_id", sa.UUID(), nullable=True))
    if not fk_exists("samples", "fk_samples_rfq_id"):
        op.create_foreign_key(
            "fk_samples_rfq_id",
            "samples",
            "rfqs",
            ["rfq_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if not column_exists("orders", "lead_id"):
        op.add_column("orders", sa.Column("lead_id", sa.UUID(), nullable=True))
    if not fk_exists("orders", "fk_orders_lead_id"):
        op.create_foreign_key(
            "fk_orders_lead_id",
            "orders",
            "leads",
            ["lead_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    op.drop_constraint("fk_orders_lead_id", "orders", type_="foreignkey")
    op.drop_column("orders", "lead_id")

    op.drop_constraint("fk_samples_rfq_id", "samples", type_="foreignkey")
    op.drop_column("samples", "rfq_id")

    op.drop_column("rfq_partner_candidates", "product_fit")
    op.drop_column("rfq_partner_candidates", "certification_status")
    op.drop_column("rfq_partner_candidates", "sample_available")
    op.drop_column("rfq_partner_candidates", "partner_price_range")
    op.drop_column("rfq_partner_candidates", "lead_time_days")
    op.drop_column("rfq_partner_candidates", "partner_moq")
    op.drop_column("rfq_partner_candidates", "capability_level")
    op.drop_column("rfq_partner_candidates", "is_preferred")

    op.drop_column("rfq_items", "shipping_requirement")
    op.drop_column("rfq_items", "packaging_requirement")
    op.drop_column("rfq_items", "required_certifications")
    op.drop_column("rfq_items", "target_price")
