"""D6.4 quote PDF export metadata migration."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.migrations.schema_util import table_exists

revision = "0008_quote_pdf_exports"
down_revision = "0007_quote_crud_versioning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if table_exists("quote_pdf_exports"):
        return

    op.create_table(
        "quote_pdf_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quote_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("export_type", sa.String(length=32), nullable=False, server_default="customer_pdf"),
        sa.Column("file_name", sa.String(length=256), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("content_type", sa.String(length=64), nullable=False, server_default="application/pdf"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="generated"),
        sa.Column("exported_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["quote_version_id"], ["quote_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["exported_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_pdf_exports_quote_id", "quote_pdf_exports", ["quote_id"])


def downgrade() -> None:
    if table_exists("quote_pdf_exports"):
        op.drop_table("quote_pdf_exports")
