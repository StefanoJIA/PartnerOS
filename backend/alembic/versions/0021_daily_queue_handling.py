"""Persist daily queue handling records."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0021_daily_queue_handling"
down_revision = "0020_market_response_reviews"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("daily_queue_handling_records"):
        return

    op.create_table(
        "daily_queue_handling_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("queue_item_id", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("source_path", sa.String(length=1024), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("partner_focus", sa.String(length=128), nullable=True),
        sa.Column("product_focus", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("customer_or_account", sa.String(length=255), nullable=True),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("handling_status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("blocked_reason", sa.Text(), nullable=True),
        sa.Column("internal_note", sa.Text(), nullable=True),
        sa.Column("decision_summary", sa.Text(), nullable=True),
        sa.Column("last_action", sa.String(length=64), nullable=True),
        sa.Column("action_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("handling_events", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("queue_item_id", name="uq_daily_queue_handling_queue_item_id"),
    )
    op.create_index("ix_daily_queue_handling_queue_item_id", "daily_queue_handling_records", ["queue_item_id"])
    op.create_index("ix_daily_queue_handling_source_type", "daily_queue_handling_records", ["source_type"])
    op.create_index("ix_daily_queue_handling_source_id", "daily_queue_handling_records", ["source_id"])
    op.create_index("ix_daily_queue_handling_category", "daily_queue_handling_records", ["category"])
    op.create_index("ix_daily_queue_handling_priority", "daily_queue_handling_records", ["priority"])
    op.create_index("ix_daily_queue_handling_partner_focus", "daily_queue_handling_records", ["partner_focus"])
    op.create_index("ix_daily_queue_handling_owner", "daily_queue_handling_records", ["owner"])
    op.create_index("ix_daily_queue_handling_status", "daily_queue_handling_records", ["handling_status"])
    op.create_index("ix_daily_queue_handling_follow_up_date", "daily_queue_handling_records", ["follow_up_date"])


def downgrade() -> None:
    if table_exists("daily_queue_handling_records"):
        op.drop_table("daily_queue_handling_records")
