"""D7.8 feedback operations fields."""

from alembic import op
import sqlalchemy as sa


revision = "0016_feedback_ops"
down_revision = "0015_feedback_tickets"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not column_exists("feedback_tickets", "internal_owner"):
        op.add_column("feedback_tickets", sa.Column("internal_owner", sa.String(length=255), nullable=True))


def downgrade() -> None:
    if column_exists("feedback_tickets", "internal_owner"):
        op.drop_column("feedback_tickets", "internal_owner")
