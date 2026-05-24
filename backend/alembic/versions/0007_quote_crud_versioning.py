"""D6.3 quote CRUD & versioning migration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import table_exists

revision = "0007_quote_crud_versioning"
down_revision = "0006_product_catalog_pricing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists("quotes"):
        return

    op.create_table(
        "quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_number", sa.String(length=32), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sales_owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quote_date", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="internal_review"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("default_incoterm", sa.String(length=16), nullable=True),
        sa.Column("payment_terms", sa.Text(), nullable=True),
        sa.Column("shipping_terms", sa.Text(), nullable=True),
        sa.Column("bill_to_name", sa.String(length=256), nullable=True),
        sa.Column("bill_to_company", sa.String(length=256), nullable=True),
        sa.Column("bill_to_address", sa.Text(), nullable=True),
        sa.Column("ship_to_name", sa.String(length=256), nullable=True),
        sa.Column("ship_to_company", sa.String(length=256), nullable=True),
        sa.Column("ship_to_address", sa.Text(), nullable=True),
        sa.Column("customer_notes", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("source_quote_input_contract_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("adjustment_total", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("tax_total", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("grand_total", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("manual_sent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("send_channel", sa.String(length=64), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sales_owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sent_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quote_number", name="uq_quotes_quote_number"),
    )
    op.create_index("ix_quotes_status", "quotes", ["status"])
    op.create_index("ix_quotes_quote_number", "quotes", ["quote_number"])
    op.create_index("ix_quotes_company_id", "quotes", ["company_id"])
    op.create_index("ix_quotes_lead_id", "quotes", ["lead_id"])

    op.create_table(
        "quote_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("version_label", sa.String(length=128), nullable=True),
        sa.Column("version_type", sa.String(length=32), nullable=False, server_default="revised"),
        sa.Column("created_from_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_from_version_id"], ["quote_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quote_id", "version_number", name="uq_quote_version_number"),
    )
    op.create_index("ix_quote_versions_quote_id", "quote_versions", ["quote_id"])

    op.create_table(
        "quote_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_catalog_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("internal_sku", sa.String(length=64), nullable=True),
        sa.Column("partner_product_code", sa.String(length=64), nullable=True),
        sa.Column("manual_product_name", sa.String(length=512), nullable=True),
        sa.Column("product_name", sa.String(length=512), nullable=False),
        sa.Column("product_category", sa.String(length=64), nullable=True),
        sa.Column("description_customer", sa.Text(), nullable=True),
        sa.Column("description_internal", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("uom", sa.String(length=16), nullable=False, server_default="EA"),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("final_unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("total_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("incoterm", sa.String(length=16), nullable=True),
        sa.Column("pricing_source", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("pricing_strategy", sa.String(length=32), nullable=True),
        sa.Column("discount_type", sa.String(length=16), nullable=True),
        sa.Column("discount_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("color_finish", sa.String(length=128), nullable=True),
        sa.Column("size_dimension", sa.String(length=128), nullable=True),
        sa.Column("attributes_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cost_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pricing_breakdown_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("customer_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("internal_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("estimated_margin", sa.Numeric(8, 4), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("requires_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quote_version_id"], ["quote_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_catalog_id"], ["product_catalog.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_line_items_quote_id", "quote_line_items", ["quote_id"])
    op.create_index("ix_quote_line_items_partner_id", "quote_line_items", ["partner_id"])

    op.create_table(
        "quote_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("percentage", sa.Numeric(8, 4), nullable=True),
        sa.Column("taxable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("customer_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_adjustments_quote_id", "quote_adjustments", ["quote_id"])

    op.create_table(
        "quote_terms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_terms", sa.Text(), nullable=True),
        sa.Column("shipping_terms", sa.Text(), nullable=True),
        sa.Column("validity_terms", sa.Text(), nullable=True),
        sa.Column("warranty_terms", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quote_id", name="uq_quote_terms_quote_id"),
    )


def downgrade() -> None:
    for name in ("quote_terms", "quote_adjustments", "quote_line_items", "quote_versions", "quotes"):
        if table_exists(name):
            op.drop_table(name)
