"""supplier network commercial loop extensions

Revision ID: 0032_supplier_network
Revises: 0031_platform_intelligence
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0032_supplier_network"
down_revision = "0031_platform_intelligence"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    discovery_cols = (
        ("source_url", sa.String(length=512)),
        ("factory_address", sa.Text()),
        ("contacts_json", postgresql.JSONB(astext_type=sa.Text())),
        ("pricing_doc_status", sa.String(length=64)),
        ("data_rights_status", sa.String(length=64)),
        ("source_review_status", sa.String(length=64)),
        ("retrieved_at", sa.DateTime(timezone=True)),
        ("usage_restrictions", sa.Text()),
        ("domain_key", sa.String(length=255)),
        ("dedup_fingerprint", sa.String(length=128)),
    )
    if table_exists("supplier_discovery_records"):
        for col_name, col_type in discovery_cols:
            if not column_exists("supplier_discovery_records", col_name):
                op.add_column("supplier_discovery_records", sa.Column(col_name, col_type, nullable=True))
        existing_indexes = {idx["name"] for idx in sa.inspect(op.get_bind()).get_indexes("supplier_discovery_records")}
        if "ix_supplier_discovery_records_domain_key" not in existing_indexes:
            op.create_index("ix_supplier_discovery_records_domain_key", "supplier_discovery_records", ["domain_key"])
        if "ix_supplier_discovery_records_dedup_fingerprint" not in existing_indexes:
            op.create_index(
                "ix_supplier_discovery_records_dedup_fingerprint", "supplier_discovery_records", ["dedup_fingerprint"]
            )

    benchmark_cols = (
        ("competitor_capability", sa.Text()),
        ("partneros_existing", sa.Text()),
        ("gap_description", sa.Text()),
        ("target_user", sa.String(length=128)),
        ("business_value", sa.Text()),
        ("implementation_cost", sa.String(length=32)),
        ("build_action", sa.String(length=32)),
    )
    if table_exists("platform_benchmark_records"):
        for col_name, col_type in benchmark_cols:
            if not column_exists("platform_benchmark_records", col_name):
                op.add_column("platform_benchmark_records", sa.Column(col_name, col_type, nullable=True))

    channel_cols = (
        ("qualified_project_count", sa.Integer()),
        ("cycle_days_avg", sa.Integer()),
        ("supplier_coverage_pct", sa.Numeric(5, 2)),
        ("lost_reasons_json", postgresql.JSONB(astext_type=sa.Text())),
    )
    if table_exists("channel_intelligence_metrics"):
        for col_name, col_type in channel_cols:
            if not column_exists("channel_intelligence_metrics", col_name):
                op.add_column("channel_intelligence_metrics", sa.Column(col_name, col_type, nullable=True))

    if not table_exists("supplier_sample_evaluations"):
        op.create_table(
            "supplier_sample_evaluations",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("supplier_discovery_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("project_request_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("product_catalog_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("template_key", sa.String(length=64), nullable=False, server_default="generic"),
            sa.Column("request_date", sa.Date(), nullable=True),
            sa.Column("shipment_date", sa.Date(), nullable=True),
            sa.Column("receipt_date", sa.Date(), nullable=True),
            sa.Column("test_items_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("results_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("file_refs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("issues", sa.Text(), nullable=True),
            sa.Column("corrective_action", sa.Text(), nullable=True),
            sa.Column("overall_result", sa.String(length=32), nullable=True),
            sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("reviewer_notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["supplier_discovery_id"], ["supplier_discovery_records.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["project_request_id"], ["customer_project_requests.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["product_catalog_id"], ["product_catalog.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_supplier_sample_evaluations_supplier_discovery_id",
            "supplier_sample_evaluations",
            ["supplier_discovery_id"],
        )
        op.create_index(
            "ix_supplier_sample_evaluations_project_request_id",
            "supplier_sample_evaluations",
            ["project_request_id"],
        )

    if not table_exists("supplier_selection_snapshots"):
        op.create_table(
            "supplier_selection_snapshots",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("project_request_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("selected_candidate_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("selected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("selected_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["project_request_id"], ["customer_project_requests.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["selected_candidate_id"], ["project_request_supplier_candidates.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(["selected_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("project_request_id", name="uq_supplier_selection_snapshot_request"),
        )


def downgrade() -> None:
    if table_exists("supplier_selection_snapshots"):
        op.drop_table("supplier_selection_snapshots")
    if table_exists("supplier_sample_evaluations"):
        op.drop_table("supplier_sample_evaluations")
