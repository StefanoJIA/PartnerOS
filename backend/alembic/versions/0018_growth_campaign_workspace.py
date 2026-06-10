"""D8.14 growth campaign workspace."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0018_growth_campaign_workspace"
down_revision = "0017_order_resources"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("growth_campaigns"):
        return

    op.create_table(
        "growth_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("partner_focus", sa.String(length=128), nullable=False),
        sa.Column("product_focus", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("target_segment", sa.String(length=255), nullable=True),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="planned"),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("next_action", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growth_campaigns_status", "growth_campaigns", ["status"])
    op.create_index("ix_growth_campaigns_partner_focus", "growth_campaigns", ["partner_focus"])

    op.create_table(
        "growth_campaign_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("task_type", sa.String(length=64), nullable=False, server_default="manual_outreach"),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="zh"),
        sa.Column("draft_subject", sa.String(length=512), nullable=True),
        sa.Column("draft_body", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="planned"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["growth_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_growth_campaign_tasks_campaign_id", "growth_campaign_tasks", ["campaign_id"])
    op.create_index("ix_growth_campaign_tasks_company_id", "growth_campaign_tasks", ["company_id"])
    op.create_index("ix_growth_campaign_tasks_contact_id", "growth_campaign_tasks", ["contact_id"])
    op.create_index("ix_growth_campaign_tasks_status", "growth_campaign_tasks", ["status"])


def downgrade() -> None:
    if table_exists("growth_campaign_tasks"):
        op.drop_table("growth_campaign_tasks")
    if table_exists("growth_campaigns"):
        op.drop_table("growth_campaigns")
