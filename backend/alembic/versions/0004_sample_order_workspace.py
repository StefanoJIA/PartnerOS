"""Sample/order workspace fields."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import column_exists, fk_exists, index_exists

revision = "0004_sample_order_workspace"
down_revision = "0003_rfq_workspace"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not column_exists("samples", "shipping_destination"):
        op.add_column("samples", sa.Column("shipping_destination", sa.Text(), nullable=True))
    if not column_exists("samples", "feedback_date"):
        op.add_column("samples", sa.Column("feedback_date", sa.Date(), nullable=True))
    if not column_exists("samples", "interest_level"):
        op.add_column("samples", sa.Column("interest_level", sa.String(length=64), nullable=True))
    if not column_exists("samples", "next_action"):
        op.add_column("samples", sa.Column("next_action", sa.Text(), nullable=True))
    if not column_exists("orders", "sample_id"):
        op.add_column(
            "orders",
            sa.Column("sample_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
    if not fk_exists("orders", "fk_orders_sample_id"):
        op.create_foreign_key(
            "fk_orders_sample_id",
            "orders",
            "samples",
            ["sample_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not index_exists("orders", "ix_orders_sample_id"):
        op.create_index("ix_orders_sample_id", "orders", ["sample_id"])


def downgrade() -> None:
    op.drop_index("ix_orders_sample_id", table_name="orders")
    op.drop_constraint("fk_orders_sample_id", "orders", type_="foreignkey")
    op.drop_column("orders", "sample_id")
    op.drop_column("samples", "next_action")
    op.drop_column("samples", "interest_level")
    op.drop_column("samples", "feedback_date")
    op.drop_column("samples", "shipping_destination")
