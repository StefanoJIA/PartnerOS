from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None

Base = declarative_base()


def get_engine() -> Engine:
    """Lazy SQLAlchemy engine; requires DATABASE_URL in settings."""
    global _engine
    if _engine is not None:
        return _engine
    url = (get_settings().DATABASE_URL or "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not configured. From the backend directory run: "
            "python scripts/init_local_env.py then edit .env, or set DATABASE_URL."
        )
    _engine = create_engine(url, pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _session_factory


def reset_engine_cache() -> None:
    """Dispose engine (tests only)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_db() -> Generator[Session, None, None]:
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    finally:
        db.close()


def __getattr__(name: str) -> Any:
    """Backward compatibility: SessionLocal as callable factory (deprecated)."""
    if name == "SessionLocal":
        return get_session_factory()
    if name == "engine":
        return get_engine()
    raise AttributeError(name)
