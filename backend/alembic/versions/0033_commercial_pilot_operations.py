"""commercial pilot operations extensions

Revision ID: 0033_commercial_pilot
Revises: 0032_supplier_network
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0033_commercial_pilot"
down_revision = "0032_supplier_network"
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
        ("relationship_type", sa.String(length=64)),
        ("evidence_status", sa.String(length=64)),
        ("manufacturing_region", sa.String(length=128)),
    )
    if table_exists("supplier_discovery_records"):
        for col_name, col_type in discovery_cols:
            if not column_exists("supplier_discovery_records", col_name):
                op.add_column("supplier_discovery_records", sa.Column(col_name, col_type, nullable=True))
        existing_indexes = {idx["name"] for idx in sa.inspect(op.get_bind()).get_indexes("supplier_discovery_records")}
        if "ix_supplier_discovery_records_relationship_type" not in existing_indexes:
            op.create_index(
                "ix_supplier_discovery_records_relationship_type",
                "supplier_discovery_records",
                ["relationship_type"],
            )

    if not table_exists("supplier_development_tasks"):
        op.create_table(
            "supplier_development_tasks",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("supplier_discovery_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("task_type", sa.String(length=64), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("priority", sa.String(length=8), nullable=False, server_default="P2"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
            sa.Column("depends_on_task_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("result_summary", sa.Text(), nullable=True),
            sa.Column("email_draft_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("checklist_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["supplier_discovery_id"], ["supplier_discovery_records.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_supplier_development_tasks_supplier_discovery_id",
            "supplier_development_tasks",
            ["supplier_discovery_id"],
        )

    if not table_exists("category_coverage_assessments"):
        op.create_table(
            "category_coverage_assessments",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("industry_vertical", sa.String(length=64), nullable=False),
            sa.Column("assessment_label", sa.String(length=128), nullable=False),
            sa.Column("customer_needs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("coverage_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("gaps_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("risk_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("suggested_actions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("linked_evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_category_coverage_assessments_industry_vertical",
            "category_coverage_assessments",
            ["industry_vertical"],
        )

    if not table_exists("commercial_pilot_runs"):
        op.create_table(
            "commercial_pilot_runs",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("pilot_code", sa.String(length=64), nullable=False),
            sa.Column("pilot_name", sa.String(length=255), nullable=False),
            sa.Column("industry_vertical", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
            sa.Column("synthetic_customer_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("requirements_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("candidate_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("selection_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("gap_tasks_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("project_request_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("market_response_review_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("scenario_pricing_blocked", sa.Boolean(), nullable=False, server_default="true"),
            sa.Column("result_summary", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["project_request_id"], ["customer_project_requests.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["market_response_review_id"], ["market_response_reviews.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("pilot_code", name="uq_commercial_pilot_runs_pilot_code"),
        )


def downgrade() -> None:
    if table_exists("commercial_pilot_runs"):
        op.drop_table("commercial_pilot_runs")
    if table_exists("category_coverage_assessments"):
        op.drop_table("category_coverage_assessments")
    if table_exists("supplier_development_tasks"):
        op.drop_table("supplier_development_tasks")
    if table_exists("supplier_discovery_records"):
        for col in ("manufacturing_region", "evidence_status", "relationship_type"):
            if column_exists("supplier_discovery_records", col):
                op.drop_column("supplier_discovery_records", col)
