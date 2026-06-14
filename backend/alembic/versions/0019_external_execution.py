"""External execution collaboration workspace."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0019_external_execution"
down_revision = "0018_growth_campaign_workspace"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if table_exists("external_execution_actions"):
        return

    op.create_table(
        "external_execution_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(length=96), nullable=False),
        sa.Column("target_partner_system", sa.String(length=255), nullable=False),
        sa.Column("partner_focus", sa.String(length=128), nullable=True),
        sa.Column("product_focus", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("dependency", sa.Text(), nullable=True),
        sa.Column("next_step", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("response_summary", sa.Text(), nullable=True),
        sa.Column("risk_notes", sa.Text(), nullable=True),
        sa.Column("blocker_notes", sa.Text(), nullable=True),
        sa.Column("redacted_credential_status", sa.String(length=96), nullable=True),
        sa.Column("staging_readiness_key", sa.String(length=96), nullable=True),
        sa.Column("pilot_readiness_key", sa.String(length=96), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_external_execution_actions_action_type", "external_execution_actions", ["action_type"])
    op.create_index("ix_external_execution_actions_status", "external_execution_actions", ["status"])
    op.create_index("ix_external_execution_actions_partner_focus", "external_execution_actions", ["partner_focus"])
    op.create_index("ix_external_execution_actions_due_date", "external_execution_actions", ["due_date"])


def downgrade() -> None:
    if table_exists("external_execution_actions"):
        op.drop_table("external_execution_actions")
