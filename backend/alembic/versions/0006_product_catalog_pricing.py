"""D6.2 product catalog & pricing foundation migration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import column_exists, table_exists

revision = "0006_product_catalog_pricing"
down_revision = "0005_company_enrichment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not column_exists("manufacturing_partners", "partner_code"):
        op.add_column("manufacturing_partners", sa.Column("partner_code", sa.String(length=32), nullable=True))
        op.create_index("ix_manufacturing_partners_partner_code", "manufacturing_partners", ["partner_code"], unique=True)
    if not column_exists("manufacturing_partners", "default_incoterm"):
        op.add_column("manufacturing_partners", sa.Column("default_incoterm", sa.String(length=16), nullable=True))
    if not column_exists("manufacturing_partners", "default_currency"):
        op.add_column(
            "manufacturing_partners",
            sa.Column("default_currency", sa.String(length=3), nullable=True, server_default="USD"),
        )
    if not column_exists("manufacturing_partners", "catalog_status"):
        op.add_column(
            "manufacturing_partners",
            sa.Column("catalog_status", sa.String(length=32), nullable=False, server_default="active"),
        )

    if table_exists("product_catalog"):
        return

    op.create_table(
        "product_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("internal_sku", sa.String(length=64), nullable=False),
        sa.Column("partner_product_code", sa.String(length=64), nullable=True),
        sa.Column("product_name", sa.String(length=512), nullable=False),
        sa.Column("product_category", sa.String(length=64), nullable=False),
        sa.Column("product_family", sa.String(length=128), nullable=True),
        sa.Column("description_customer", sa.Text(), nullable=True),
        sa.Column("description_internal", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("default_uom", sa.String(length=16), nullable=False, server_default="EA"),
        sa.Column("base_currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("default_incoterm", sa.String(length=16), nullable=True),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("attributes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("internal_sku", name="uq_product_catalog_internal_sku"),
        sa.UniqueConstraint("partner_id", "partner_product_code", name="uq_product_catalog_partner_code"),
    )
    op.create_index("ix_product_catalog_partner_id", "product_catalog", ["partner_id"])
    op.create_index("ix_product_catalog_product_category", "product_catalog", ["product_category"])
    op.create_index("ix_product_catalog_status", "product_catalog", ["status"])

    op.create_table(
        "product_cost_models",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cost_currency", sa.String(length=3), nullable=False, server_default="CNY"),
        sa.Column("unit_material_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("unit_weight", sa.Numeric(12, 4), nullable=True),
        sa.Column("ocean_freight_unit_price", sa.Numeric(12, 4), nullable=True),
        sa.Column("domestic_transport_cost", sa.Numeric(18, 4), nullable=True),
        sa.Column("domestic_profit_rate", sa.Numeric(8, 4), nullable=True),
        sa.Column("fob_cost_usd", sa.Numeric(18, 4), nullable=True),
        sa.Column("ddp_cost_usd", sa.Numeric(18, 4), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["product_catalog.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_cost_models_product_id", "product_cost_models", ["product_id"])

    op.create_table(
        "product_price_tiers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("min_qty", sa.Integer(), nullable=False),
        sa.Column("max_qty", sa.Integer(), nullable=True),
        sa.Column("incoterm", sa.String(length=16), nullable=False),
        sa.Column("base_unit_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("adjustment_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("final_unit_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("pricing_strategy", sa.String(length=32), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["product_catalog.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_price_tiers_product_id", "product_price_tiers", ["product_id"])
    op.create_index("ix_product_price_tiers_incoterm", "product_price_tiers", ["incoterm"])

    op.create_table(
        "margin_strategy_tiers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strategy_code", sa.String(length=32), nullable=False),
        sa.Column("strategy_name", sa.String(length=64), nullable=True),
        sa.Column("min_qty", sa.Integer(), nullable=False),
        sa.Column("max_qty", sa.Integer(), nullable=True),
        sa.Column("multiplier", sa.Numeric(8, 4), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_code", "min_qty", "max_qty", name="uq_margin_strategy_tier"),
    )
    op.create_index("ix_margin_strategy_tiers_strategy_code", "margin_strategy_tiers", ["strategy_code"])

    op.create_table(
        "fx_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("quote_currency", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("is_manual_override", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("base_currency", "quote_currency", "rate_date", name="uq_fx_rate_pair_date"),
    )
    op.create_index("ix_fx_rates_rate_date", "fx_rates", ["rate_date"])


def downgrade() -> None:
    if table_exists("fx_rates"):
        op.drop_table("fx_rates")
    if table_exists("margin_strategy_tiers"):
        op.drop_table("margin_strategy_tiers")
    if table_exists("product_price_tiers"):
        op.drop_table("product_price_tiers")
    if table_exists("product_cost_models"):
        op.drop_table("product_cost_models")
    if table_exists("product_catalog"):
        op.drop_table("product_catalog")
    if column_exists("manufacturing_partners", "catalog_status"):
        op.drop_column("manufacturing_partners", "catalog_status")
    if column_exists("manufacturing_partners", "default_currency"):
        op.drop_column("manufacturing_partners", "default_currency")
    if column_exists("manufacturing_partners", "default_incoterm"):
        op.drop_column("manufacturing_partners", "default_incoterm")
    if column_exists("manufacturing_partners", "partner_code"):
        op.drop_index("ix_manufacturing_partners_partner_code", table_name="manufacturing_partners")
        op.drop_column("manufacturing_partners", "partner_code")
