"""supplier discovery workbench

Revision ID: 0029_supplier_discovery
Revises: 0028_benchmark_knowledge
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0029_supplier_discovery"
down_revision = "0028_benchmark_knowledge"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("supplier_discovery_records"):
        return

    op.create_table(
        "supplier_discovery_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(length=512), nullable=False),
        sa.Column("brand_name", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=128), nullable=True),
        sa.Column("categories", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("certifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("moq_notes", sa.Text(), nullable=True),
        sa.Column("sample_policy", sa.Text(), nullable=True),
        sa.Column("lead_time_notes", sa.Text(), nullable=True),
        sa.Column("export_markets", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("doc_completeness_pct", sa.Integer(), nullable=True),
        sa.Column("contact_status", sa.String(length=64), nullable=True),
        sa.Column("risk_level", sa.String(length=32), nullable=True),
        sa.Column("data_source", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="discovered"),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("qualification_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_supplier_discovery_records_company_name", "supplier_discovery_records", ["company_name"])
    op.create_index("ix_supplier_discovery_records_status", "supplier_discovery_records", ["status"])
    op.create_index("ix_supplier_discovery_records_owner_user_id", "supplier_discovery_records", ["owner_user_id"])
    op.create_index("ix_supplier_discovery_records_partner_id", "supplier_discovery_records", ["partner_id"])


def downgrade() -> None:
    if table_exists("supplier_discovery_records"):
        op.drop_table("supplier_discovery_records")
