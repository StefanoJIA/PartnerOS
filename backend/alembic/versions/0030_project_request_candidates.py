"""project request supplier candidates

Revision ID: 0030_project_request_candidates
Revises: 0029_supplier_discovery
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0030_project_request_candidates"
down_revision = "0029_supplier_discovery"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("project_request_supplier_candidates"):
        return

    op.create_table(
        "project_request_supplier_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_source_type", sa.String(length=32), nullable=False),
        sa.Column("candidate_ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_catalog_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("benchmark_brand_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("supplier_discovery_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("candidate_role", sa.String(length=32), nullable=False, server_default="alternate"),
        sa.Column("display_name", sa.String(length=512), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("fit_dimensions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("evidence_quality", sa.String(length=32), nullable=True),
        sa.Column("overall_fit_status", sa.String(length=32), nullable=True),
        sa.Column("eligible_for_formal_quote", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("operator_decision", sa.String(length=32), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("is_auto_recommended", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["project_request_id"], ["customer_project_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_catalog_id"], ["product_catalog.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["benchmark_brand_id"], ["benchmark_brands.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["supplier_discovery_id"], ["supplier_discovery_records.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_request_id",
            "candidate_source_type",
            "candidate_ref_id",
            name="uq_project_request_candidate_ref",
        ),
    )
    op.create_index(
        "ix_project_request_supplier_candidates_project_request_id",
        "project_request_supplier_candidates",
        ["project_request_id"],
    )


def downgrade() -> None:
    if table_exists("project_request_supplier_candidates"):
        op.drop_table("project_request_supplier_candidates")
