"""D7.2 customer order CRUD MVP."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import table_exists

revision = "0010_order_crud_mvp"
down_revision = "0009_quote_send_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists("customer_orders"):
        return

    op.create_table(
        "customer_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("source_quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_quote_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_pdf_export_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_delivery_log_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=48), nullable=False, server_default="pending_customer_confirmation"),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("customer_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("customer_confirmation_method", sa.String(length=32), nullable=True),
        sa.Column("customer_confirmation_note", sa.Text(), nullable=True),
        sa.Column("bill_to_name", sa.String(length=256), nullable=True),
        sa.Column("bill_to_company", sa.String(length=256), nullable=True),
        sa.Column("bill_to_address", sa.Text(), nullable=True),
        sa.Column("ship_to_name", sa.String(length=256), nullable=True),
        sa.Column("ship_to_company", sa.String(length=256), nullable=True),
        sa.Column("ship_to_address", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("adjustment_total", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("grand_total", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("payment_terms", sa.Text(), nullable=True),
        sa.Column("shipping_terms", sa.Text(), nullable=True),
        sa.Column("order_input_contract_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("readiness_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("customer_notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_quote_id"], ["quotes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_quote_version_id"], ["quote_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_pdf_export_id"], ["quote_pdf_exports.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_delivery_log_id"], ["quote_delivery_logs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number", name="uq_customer_orders_order_number"),
    )
    op.create_index("ix_customer_orders_order_number", "customer_orders", ["order_number"])
    op.create_index("ix_customer_orders_source_quote_id", "customer_orders", ["source_quote_id"])
    op.create_index("ix_customer_orders_status", "customer_orders", ["status"])
    op.create_index("ix_customer_orders_company_id", "customer_orders", ["company_id"])
    op.create_index("ix_customer_orders_order_date", "customer_orders", ["order_date"])

    op.create_table(
        "order_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_quote_line_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_catalog_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("internal_sku", sa.String(length=64), nullable=True),
        sa.Column("partner_product_code", sa.String(length=64), nullable=True),
        sa.Column("product_name", sa.String(length=512), nullable=False),
        sa.Column("product_category", sa.String(length=64), nullable=True),
        sa.Column("description_customer", sa.Text(), nullable=True),
        sa.Column("description_internal", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("uom", sa.String(length=16), nullable=False, server_default="EA"),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("total_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("incoterm", sa.String(length=16), nullable=True),
        sa.Column("color_finish", sa.String(length=128), nullable=True),
        sa.Column("size_dimension", sa.String(length=128), nullable=True),
        sa.Column("attributes_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("customer_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("supplier_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["customer_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_quote_line_item_id"], ["quote_line_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_catalog_id"], ["product_catalog.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_line_items_order_id", "order_line_items", ["order_id"])
    op.create_index("ix_order_line_items_partner_id", "order_line_items", ["partner_id"])


def downgrade() -> None:
    if table_exists("order_line_items"):
        op.drop_table("order_line_items")
    if table_exists("customer_orders"):
        op.drop_table("customer_orders")
