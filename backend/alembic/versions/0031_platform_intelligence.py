"""platform benchmark and channel intelligence

Revision ID: 0031_platform_intelligence
Revises: 0030_project_request_candidates
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0031_platform_intelligence"
down_revision = "0030_project_request_candidates"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not table_exists("platform_benchmark_records"):
        op.create_table(
            "platform_benchmark_records",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("platform_name", sa.String(length=128), nullable=False),
            sa.Column("capability_area", sa.String(length=128), nullable=False),
            sa.Column("capability_description", sa.Text(), nullable=True),
            sa.Column("partneros_has", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("partneros_gap_notes", sa.Text(), nullable=True),
            sa.Column("build_recommended", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("build_priority", sa.String(length=8), nullable=False, server_default="P2"),
            sa.Column("evidence_source", sa.String(length=255), nullable=True),
            sa.Column("evidence_url", sa.String(length=512), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_platform_benchmark_records_platform_name", "platform_benchmark_records", ["platform_name"])

    if not table_exists("channel_intelligence_metrics"):
        op.create_table(
            "channel_intelligence_metrics",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("channel_source", sa.String(length=64), nullable=False),
            sa.Column("period_label", sa.String(length=32), nullable=False),
            sa.Column("lead_count", sa.Integer(), nullable=True),
            sa.Column("quote_count", sa.Integer(), nullable=True),
            sa.Column("win_count", sa.Integer(), nullable=True),
            sa.Column("lead_quality_score", sa.Numeric(5, 2), nullable=True),
            sa.Column("quote_rate", sa.Numeric(5, 4), nullable=True),
            sa.Column("win_rate", sa.Numeric(5, 4), nullable=True),
            sa.Column("data_source", sa.String(length=64), nullable=False, server_default="manual"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("metrics_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_channel_intelligence_metrics_channel_source", "channel_intelligence_metrics", ["channel_source"]
        )


def downgrade() -> None:
    for table in ("channel_intelligence_metrics", "platform_benchmark_records"):
        if table_exists(table):
            op.drop_table(table)
