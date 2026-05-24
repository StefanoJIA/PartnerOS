"""D7.3 order customer confirmations migration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import table_exists

revision = "0011_order_confirmations"
down_revision = "0010_order_crud_mvp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists("order_confirmations"):
        return

    op.create_table(
        "order_confirmations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("confirmation_type", sa.String(length=32), nullable=False),
        sa.Column("confirmation_strength", sa.String(length=16), nullable=False),
        sa.Column("confirmed_by_name", sa.String(length=256), nullable=True),
        sa.Column("confirmed_by_email", sa.String(length=256), nullable=True),
        sa.Column("confirmed_by_company", sa.String(length=256), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_channel", sa.String(length=64), nullable=True),
        sa.Column("evidence_reference", sa.Text(), nullable=True),
        sa.Column("evidence_filename", sa.String(length=512), nullable=True),
        sa.Column("evidence_storage_path", sa.String(length=1024), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("voided_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["customer_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_confirmations_order_id", "order_confirmations", ["order_id"])
    op.create_index("ix_order_confirmations_status", "order_confirmations", ["status"])


def downgrade() -> None:
    if table_exists("order_confirmations"):
        op.drop_table("order_confirmations")
