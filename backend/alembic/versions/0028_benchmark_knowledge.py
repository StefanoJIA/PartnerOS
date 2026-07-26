"""benchmark knowledge model

Revision ID: 0028_benchmark_knowledge
Revises: 0027_partner_lifecycle
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0028_benchmark_knowledge"
down_revision = "0027_partner_lifecycle"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("benchmark_brands"):
        return

    op.create_table(
        "benchmark_brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("industry_vertical", sa.String(length=128), nullable=False),
        sa.Column("country", sa.String(length=128), nullable=True),
        sa.Column("website_url", sa.String(length=512), nullable=True),
        sa.Column("relationship_disclaimer", sa.Text(), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brand_code", name="uq_benchmark_brand_code"),
    )
    op.create_index("ix_benchmark_brands_brand_code", "benchmark_brands", ["brand_code"])
    op.create_index("ix_benchmark_brands_industry_vertical", "benchmark_brands", ["industry_vertical"])

    op.create_table(
        "benchmark_product_capabilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_line", sa.String(length=255), nullable=True),
        sa.Column("capability_key", sa.String(length=128), nullable=False),
        sa.Column("capability_label", sa.String(length=255), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False, server_default="pending_verification"),
        sa.Column("source_type", sa.String(length=64), nullable=False, server_default="PUBLIC_REFERENCE"),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("retrieved_at", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["benchmark_brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brand_id", "capability_key", name="uq_benchmark_capability"),
    )
    op.create_index("ix_benchmark_product_capabilities_brand_id", "benchmark_product_capabilities", ["brand_id"])

    op.create_table(
        "benchmark_source_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("source_title", sa.String(length=512), nullable=True),
        sa.Column("retrieved_at", sa.Date(), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("excerpt_facts", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["benchmark_brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_benchmark_source_references_brand_id", "benchmark_source_references", ["brand_id"])

    op.create_table(
        "benchmark_data_rights",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("allowed_use", sa.Text(), nullable=False),
        sa.Column("prohibited_use", sa.Text(), nullable=False),
        sa.Column("logo_copy_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("catalog_copy_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("price_copy_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_reviewed_at", sa.Date(), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["benchmark_brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("brand_id"),
    )


def downgrade() -> None:
    for table in (
        "benchmark_data_rights",
        "benchmark_source_references",
        "benchmark_product_capabilities",
        "benchmark_brands",
    ):
        if table_exists(table):
            op.drop_table(table)
