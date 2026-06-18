"""add quote pricing assumptions

Revision ID: 0025_pricing_assumptions
Revises: 0024_win_loss_capture
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from datetime import date, datetime, timezone
from uuid import uuid4
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0025_pricing_assumptions"
down_revision = "0024_win_loss_capture"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pricing_assumptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assumption_key", sa.String(length=96), nullable=False),
        sa.Column("numeric_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=96), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assumption_key", "effective_from", name="uq_pricing_assumption_key_effective_from"),
    )
    op.create_index("ix_pricing_assumptions_assumption_key", "pricing_assumptions", ["assumption_key"])
    op.create_index("ix_pricing_assumptions_effective_from", "pricing_assumptions", ["effective_from"])
    op.create_index("ix_pricing_assumptions_is_active", "pricing_assumptions", ["is_active"])

    assumptions = sa.table(
        "pricing_assumptions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("assumption_key", sa.String),
        sa.column("numeric_value", sa.Numeric),
        sa.column("unit", sa.String),
        sa.column("source", sa.String),
        sa.column("effective_from", sa.Date),
        sa.column("is_active", sa.Boolean),
        sa.column("notes", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    now = datetime.now(timezone.utc)
    op.bulk_insert(
        assumptions,
        [
            {
                "id": uuid4(),
                "assumption_key": "ocean_freight_unit_price",
                "numeric_value": 22,
                "unit": "RMB/kg",
                "source": "manual_provider_quote",
                "effective_from": date.today(),
                "is_active": True,
                "notes": "Initial ocean freight provider quote. Update here when provider quote changes.",
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_pricing_assumptions_is_active", table_name="pricing_assumptions")
    op.drop_index("ix_pricing_assumptions_effective_from", table_name="pricing_assumptions")
    op.drop_index("ix_pricing_assumptions_assumption_key", table_name="pricing_assumptions")
    op.drop_table("pricing_assumptions")
