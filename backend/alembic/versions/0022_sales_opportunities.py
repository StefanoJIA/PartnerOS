"""Add sales opportunities."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0022_sales_opportunities"
down_revision = "0021_daily_queue_handling"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("sales_opportunities"):
        return

    op.create_table(
        "sales_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("opportunity_name", sa.String(length=255), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("partner_focus", sa.String(length=128), nullable=True),
        sa.Column("product_focus", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("customer_segment", sa.String(length=255), nullable=True),
        sa.Column("project_size", sa.String(length=64), nullable=True),
        sa.Column("estimated_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("decision_stage", sa.String(length=64), nullable=False, server_default="discovery"),
        sa.Column("competition", sa.Text(), nullable=True),
        sa.Column("risk", sa.Text(), nullable=True),
        sa.Column("probability", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="P2"),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("next_action", sa.Text(), nullable=True),
        sa.Column("blocker", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("expected_close_date", sa.Date(), nullable=True),
        sa.Column("won_reason", sa.Text(), nullable=True),
        sa.Column("lost_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["growth_campaigns.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["customer_orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_opportunities_campaign_id", "sales_opportunities", ["campaign_id"])
    op.create_index("ix_sales_opportunities_company_id", "sales_opportunities", ["company_id"])
    op.create_index("ix_sales_opportunities_decision_stage", "sales_opportunities", ["decision_stage"])
    op.create_index("ix_sales_opportunities_expected_close_date", "sales_opportunities", ["expected_close_date"])
    op.create_index("ix_sales_opportunities_lead_id", "sales_opportunities", ["lead_id"])
    op.create_index("ix_sales_opportunities_order_id", "sales_opportunities", ["order_id"])
    op.create_index("ix_sales_opportunities_partner_focus", "sales_opportunities", ["partner_focus"])
    op.create_index("ix_sales_opportunities_priority", "sales_opportunities", ["priority"])
    op.create_index("ix_sales_opportunities_quote_id", "sales_opportunities", ["quote_id"])
    op.create_index("ix_sales_opportunities_status", "sales_opportunities", ["status"])


def downgrade() -> None:
    if table_exists("sales_opportunities"):
        op.drop_table("sales_opportunities")
