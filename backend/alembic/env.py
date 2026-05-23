from logging.config import fileConfig

import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.core.database import Base
import app.models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _fail_migration(msg: str, *, detail_lines: list[str] | None = None) -> None:
    print(f"Alembic: {msg}", file=sys.stderr)
    if detail_lines:
        for line in detail_lines:
            print(line, file=sys.stderr)
    print(
        "\nFrom the backend directory, run:\n"
        "  python scripts/check_database_config.py\n",
        file=sys.stderr,
    )
    sys.exit(1)


def _preflight_offline() -> None:
    url = (get_settings().DATABASE_URL or "").strip()
    if not url:
        _fail_migration(
            "DATABASE_URL is not set.",
            detail_lines=[
                "Create backend/.env (copy from .env.example):",
                "  python scripts/init_local_env.py",
            ],
        )


def _preflight_online() -> None:
    from app.core.database_lifecycle import check_database

    settings = get_settings()
    url = (settings.DATABASE_URL or "").strip()
    if not url:
        _preflight_offline()
        return
    status, errors = check_database(settings)
    if status == "ready":
        return
    lines = [f"database_status={status}"] + [f"  - {e}" for e in errors if e]
    _fail_migration("cannot connect to PostgreSQL; migrations were not run.", detail_lines=lines)


def run_migrations_offline() -> None:
    url = get_settings().DATABASE_URL
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_settings().DATABASE_URL
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    _preflight_offline()
    run_migrations_offline()
else:
    _preflight_online()
    run_migrations_online()
