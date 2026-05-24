"""D6.5 quote send tracking and delivery log migration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import column_exists, table_exists

revision = "0009_quote_send_tracking"
down_revision = "0008_quote_pdf_exports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if not table_exists("quote_delivery_logs"):
        op.create_table(
            "quote_delivery_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("quote_version_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("pdf_export_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("sent_channel", sa.String(length=32), nullable=False),
            sa.Column("sent_to_name", sa.String(length=256), nullable=True),
            sa.Column("sent_to_email", sa.String(length=256), nullable=True),
            sa.Column("sent_to_company", sa.String(length=256), nullable=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("sent_by_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("manual_sent", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("follow_up_date", sa.Date(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="recorded"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["quote_version_id"], ["quote_versions.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["pdf_export_id"], ["quote_pdf_exports.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["sent_by_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_quote_delivery_logs_quote_id", "quote_delivery_logs", ["quote_id"])
        op.create_index("ix_quote_delivery_logs_follow_up_date", "quote_delivery_logs", ["follow_up_date"])

    if not column_exists("quotes", "last_delivery_log_id"):
        op.add_column(
            "quotes",
            sa.Column("last_delivery_log_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_quotes_last_delivery_log_id",
            "quotes",
            "quote_delivery_logs",
            ["last_delivery_log_id"],
            ["id"],
            ondelete="SET NULL",
        )
    if not column_exists("quotes", "follow_up_date"):
        op.add_column("quotes", sa.Column("follow_up_date", sa.Date(), nullable=True))


def downgrade() -> None:
    if column_exists("quotes", "follow_up_date"):
        op.drop_column("quotes", "follow_up_date")
    if column_exists("quotes", "last_delivery_log_id"):
        op.drop_constraint("fk_quotes_last_delivery_log_id", "quotes", type_="foreignkey")
        op.drop_column("quotes", "last_delivery_log_id")
    if table_exists("quote_delivery_logs"):
        op.drop_table("quote_delivery_logs")
