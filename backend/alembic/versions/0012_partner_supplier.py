"""D7.4 partner splits and supplier confirmations migration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import table_exists

revision = "0012_partner_supplier"
down_revision = "0011_order_confirmations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not table_exists("order_partner_splits"):
        op.create_table(
            "order_partner_splits",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("split_number", sa.String(length=32), nullable=False),
            sa.Column("split_status", sa.String(length=48), nullable=False, server_default="pending_supplier_confirmation"),
            sa.Column("partner_reference_number", sa.String(length=128), nullable=True),
            sa.Column("supplier_confirmation_status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("supplier_confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expected_production_start", sa.Date(), nullable=True),
            sa.Column("expected_ready_date", sa.Date(), nullable=True),
            sa.Column("line_item_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("subtotal", sa.Numeric(18, 2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["order_id"], ["customer_orders.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("order_id", "partner_id", name="uq_order_partner_splits_order_partner"),
        )
        op.create_index("ix_order_partner_splits_order_id", "order_partner_splits", ["order_id"])
        op.create_index("ix_order_partner_splits_partner_id", "order_partner_splits", ["partner_id"])

    if not table_exists("supplier_confirmations"):
        op.create_table(
            "supplier_confirmations",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("partner_split_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("confirmation_status", sa.String(length=32), nullable=False),
            sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("confirmed_by_name", sa.String(length=256), nullable=True),
            sa.Column("confirmed_by_email", sa.String(length=256), nullable=True),
            sa.Column("confirmation_channel", sa.String(length=64), nullable=True),
            sa.Column("inventory_confirmed", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("certification_confirmed", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("lead_time_confirmed", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("production_capacity_confirmed", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("expected_production_start", sa.Date(), nullable=True),
            sa.Column("expected_ready_date", sa.Date(), nullable=True),
            sa.Column("supplier_reference", sa.String(length=256), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
            sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("voided_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["order_id"], ["customer_orders.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["partner_split_id"], ["order_partner_splits.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_supplier_confirmations_order_id", "supplier_confirmations", ["order_id"])
        op.create_index("ix_supplier_confirmations_partner_split_id", "supplier_confirmations", ["partner_split_id"])
        op.create_index("ix_supplier_confirmations_status", "supplier_confirmations", ["status"])


def downgrade() -> None:
    if table_exists("supplier_confirmations"):
        op.drop_table("supplier_confirmations")
    if table_exists("order_partner_splits"):
        op.drop_table("order_partner_splits")
