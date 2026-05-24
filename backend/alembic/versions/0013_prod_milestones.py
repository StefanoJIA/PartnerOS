"""D7.5 order production milestones migration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import table_exists

revision = "0013_prod_milestones"
down_revision = "0012_partner_supplier"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists("order_production_milestones"):
        return

    op.create_table(
        "order_production_milestones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("partner_split_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("milestone_type", sa.String(length=64), nullable=False),
        sa.Column("milestone_label", sa.String(length=128), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="planned"),
        sa.Column("planned_date", sa.Date(), nullable=True),
        sa.Column("actual_date", sa.Date(), nullable=True),
        sa.Column("responsible_party", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="template"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["customer_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_split_id"], ["order_partner_splits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["manufacturing_partners.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "partner_split_id",
            "milestone_type",
            name="uq_order_prod_milestones_split_type",
        ),
    )
    op.create_index("ix_order_prod_milestones_order_id", "order_production_milestones", ["order_id"])
    op.create_index("ix_order_prod_milestones_partner_split_id", "order_production_milestones", ["partner_split_id"])
    op.create_index("ix_order_prod_milestones_status", "order_production_milestones", ["status"])


def downgrade() -> None:
    if table_exists("order_production_milestones"):
        op.drop_table("order_production_milestones")
