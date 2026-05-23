"""D5.2 company public-source enrichment runs, sources, suggestions."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import table_exists

revision = "0005_company_enrichment"
down_revision = "0004_sample_order_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists("company_enrichment_runs"):
        return

    op.create_table(
        "company_enrichment_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source_scope", sa.String(length=64), nullable=False),
        sa.Column("max_pages", sa.Integer(), nullable=False),
        sa.Column("pages_fetched", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_company_enrichment_runs_company_id", "company_enrichment_runs", ["company_id"], unique=False
    )
    op.create_index("ix_company_enrichment_runs_status", "company_enrichment_runs", ["status"], unique=False)

    op.create_table(
        "company_enrichment_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("page_title", sa.String(length=512), nullable=True),
        sa.Column("page_type", sa.String(length=32), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("fetch_status", sa.String(length=32), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("content_excerpt", sa.String(length=1024), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["enrichment_run_id"], ["company_enrichment_runs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_company_enrichment_sources_enrichment_run_id",
        "company_enrichment_sources",
        ["enrichment_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_enrichment_sources_content_hash",
        "company_enrichment_sources",
        ["content_hash"],
        unique=False,
    )

    op.create_table(
        "company_enrichment_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrichment_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("suggestion_type", sa.String(length=32), nullable=False),
        sa.Column("suggested_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("evidence_source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evidence_snippet", sa.Text(), nullable=True),
        sa.Column("matched_phrase", sa.String(length=512), nullable=True),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["enrichment_run_id"], ["company_enrichment_runs.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["evidence_source_id"], ["company_enrichment_sources.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_company_enrichment_suggestions_enrichment_run_id",
        "company_enrichment_suggestions",
        ["enrichment_run_id"],
        unique=False,
    )
    op.create_index(
        "ix_company_enrichment_suggestions_review_status",
        "company_enrichment_suggestions",
        ["review_status"],
        unique=False,
    )
    op.create_index(
        "ix_company_enrichment_suggestions_suggestion_type",
        "company_enrichment_suggestions",
        ["suggestion_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("company_enrichment_suggestions")
    op.drop_table("company_enrichment_sources")
    op.drop_table("company_enrichment_runs")
