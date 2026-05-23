"""Helpers for idempotent Alembic revisions when 0001_initial uses create_all."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


def column_exists(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(c["name"] == column for c in insp.get_columns(table))


def table_exists(table: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return table in insp.get_table_names()


def fk_exists(table: str, fk_name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(fk.get("name") == fk_name for fk in insp.get_foreign_keys(table))


def index_exists(table: str, index_name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(idx.get("name") == index_name for idx in insp.get_indexes(table))
