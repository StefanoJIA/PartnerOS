"""D7.7 feedback tickets migration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import table_exists

revision = "0015_feedback_tickets"
down_revision = "0014_shipment_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists("feedback_tickets"):
        return

    op.create_table(
        "feedback_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_number", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="customer_portal"),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("feedback_type", sa.String(length=64), nullable=False, server_default="general"),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("customer_name", sa.String(length=255), nullable=True),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["customer_orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_number", name="uq_feedback_tickets_ticket_number"),
    )
    op.create_index("ix_feedback_tickets_order_id", "feedback_tickets", ["order_id"])
    op.create_index("ix_feedback_tickets_company_id", "feedback_tickets", ["company_id"])
    op.create_index("ix_feedback_tickets_status", "feedback_tickets", ["status"])


def downgrade() -> None:
    if table_exists("feedback_tickets"):
        op.drop_table("feedback_tickets")
