"""partner lifecycle status

Revision ID: 0027_partner_lifecycle
Revises: 0026_customer_project_requests
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0027_partner_lifecycle"
down_revision = "0026_customer_project_requests"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns(table_name)}
    return column_name in cols


def upgrade() -> None:
    if not column_exists("manufacturing_partners", "lifecycle_status"):
        op.add_column(
            "manufacturing_partners",
            sa.Column("lifecycle_status", sa.String(length=32), nullable=False, server_default="active"),
        )
        op.create_index("ix_manufacturing_partners_lifecycle_status", "manufacturing_partners", ["lifecycle_status"])
    if not column_exists("manufacturing_partners", "lifecycle_notes"):
        op.add_column("manufacturing_partners", sa.Column("lifecycle_notes", sa.Text(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE manufacturing_partners
            SET lifecycle_status = 'legacy',
                lifecycle_notes = COALESCE(lifecycle_notes, 'Historical reference partner — not default for new quotes or demos.')
            WHERE UPPER(COALESCE(partner_code, '')) = 'HOSUN'
            """
        )
    )


def downgrade() -> None:
    if column_exists("manufacturing_partners", "lifecycle_notes"):
        op.drop_column("manufacturing_partners", "lifecycle_notes")
    if column_exists("manufacturing_partners", "lifecycle_status"):
        op.drop_index("ix_manufacturing_partners_lifecycle_status", table_name="manufacturing_partners")
        op.drop_column("manufacturing_partners", "lifecycle_status")
