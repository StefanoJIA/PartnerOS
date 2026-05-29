"""D7.6 shipment plans migration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import table_exists

revision = "0014_shipment_plans"
down_revision = "0013_prod_milestones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not table_exists("shipment_plans"):
        op.create_table(
            "shipment_plans",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("partner_split_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("shipment_method", sa.String(length=64), nullable=True),
            sa.Column("incoterm", sa.String(length=16), nullable=True),
            sa.Column("origin", sa.String(length=255), nullable=True),
            sa.Column("destination", sa.String(length=255), nullable=True),
            sa.Column("estimated_ship_date", sa.Date(), nullable=True),
            sa.Column("estimated_arrival_date", sa.Date(), nullable=True),
            sa.Column("tracking_number", sa.String(length=128), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["order_id"], ["customer_orders.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["partner_split_id"], ["order_partner_splits.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_shipment_plans_order_id", "shipment_plans", ["order_id"])
        op.create_index("ix_shipment_plans_partner_split_id", "shipment_plans", ["partner_split_id"])
        op.create_index("ix_shipment_plans_status", "shipment_plans", ["status"])

    if not table_exists("shipment_tracking_events"):
        op.create_table(
            "shipment_tracking_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("shipment_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["shipment_plan_id"], ["shipment_plans.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_shipment_tracking_events_plan_id", "shipment_tracking_events", ["shipment_plan_id"])
        op.create_index("ix_shipment_tracking_events_status", "shipment_tracking_events", ["status"])


def downgrade() -> None:
    if table_exists("shipment_tracking_events"):
        op.drop_table("shipment_tracking_events")
    if table_exists("shipment_plans"):
        op.drop_table("shipment_plans")
