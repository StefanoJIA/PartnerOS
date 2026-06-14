"""Persist market response review queue."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0020_market_response_reviews"
down_revision = "0019_external_execution"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("market_response_reviews"):
        return

    op.create_table(
        "market_response_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("partner_focus", sa.String(length=128), nullable=False),
        sa.Column("focus_category", sa.String(length=96), nullable=False),
        sa.Column("product_focus", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("review_dimension", sa.String(length=96), nullable=False),
        sa.Column("visibility_class", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="P2"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="needs review"),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_summary", sa.Text(), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("customer_safe_summary", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("next_action", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_response_reviews_partner_focus", "market_response_reviews", ["partner_focus"])
    op.create_index("ix_market_response_reviews_focus_category", "market_response_reviews", ["focus_category"])
    op.create_index("ix_market_response_reviews_review_dimension", "market_response_reviews", ["review_dimension"])
    op.create_index("ix_market_response_reviews_visibility_class", "market_response_reviews", ["visibility_class"])
    op.create_index("ix_market_response_reviews_status", "market_response_reviews", ["status"])
    op.create_index("ix_market_response_reviews_priority", "market_response_reviews", ["priority"])
    op.create_index("ix_market_response_reviews_due_date", "market_response_reviews", ["due_date"])


def downgrade() -> None:
    if table_exists("market_response_reviews"):
        op.drop_table("market_response_reviews")
