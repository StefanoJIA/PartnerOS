"""customer project request intake

Revision ID: 0026_customer_project_requests
Revises: 0025_pricing_assumptions
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0026_customer_project_requests"
down_revision = "0025_pricing_assumptions"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("customer_project_requests"):
        return

    op.create_table(
        "customer_project_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_reference", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="submitted"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="customer_site"),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("company_name_text", sa.String(length=255), nullable=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_catalog_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("product_interest", sa.String(length=512), nullable=True),
        sa.Column("quantity_min", sa.Integer(), nullable=True),
        sa.Column("quantity_max", sa.Integer(), nullable=True),
        sa.Column("target_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("delivery_region", sa.String(length=255), nullable=True),
        sa.Column("expected_date", sa.Date(), nullable=True),
        sa.Column("project_scenario", sa.Text(), nullable=True),
        sa.Column("requirements_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attachment_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fit_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("completeness_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rfq_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quote_ready_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("operator_notes", sa.Text(), nullable=True),
        sa.Column("client_ip_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_catalog_id"], ["product_catalog.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rfq_id"], ["rfqs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_reference", name="uq_customer_project_request_reference"),
        sa.UniqueConstraint("idempotency_key", name="uq_customer_project_request_idempotency"),
    )
    op.create_index("ix_customer_project_requests_status", "customer_project_requests", ["status"])
    op.create_index("ix_customer_project_requests_priority", "customer_project_requests", ["priority"])
    op.create_index("ix_customer_project_requests_source", "customer_project_requests", ["source"])
    op.create_index("ix_customer_project_requests_company_id", "customer_project_requests", ["company_id"])
    op.create_index("ix_customer_project_requests_partner_id", "customer_project_requests", ["partner_id"])
    op.create_index("ix_customer_project_requests_sku", "customer_project_requests", ["sku"])
    op.create_index("ix_customer_project_requests_owner_user_id", "customer_project_requests", ["owner_user_id"])


def downgrade() -> None:
    if not table_exists("customer_project_requests"):
        return
    op.drop_table("customer_project_requests")
