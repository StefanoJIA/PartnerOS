from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.core.database_lifecycle import check_database


def test_check_database_not_configured_message():
    st, errs = check_database(Settings(DATABASE_URL=""))
    assert st == "not_configured"
    assert errs
    assert "init_local_env" in errs[0] or "DATABASE_URL" in errs[0]


def test_check_database_auth_failed(monkeypatch):
    def _boom(*_a, **_kw):
        raise SQLAlchemyError(
            '(psycopg.OperationalError) connection failed: FATAL:  password authentication failed for user "partneros"'
        )

    monkeypatch.setattr("app.core.database_lifecycle.create_engine", _boom)
    st, errs = check_database(
        Settings(DATABASE_URL="postgresql+psycopg://partneros:wrong@127.0.0.1:5432/partneros"),
    )
    assert st == "auth_failed"
    assert any("rejected" in e.lower() for e in errs)


def test_check_database_missing_db(monkeypatch):
    def _boom(*_a, **_kw):
        raise SQLAlchemyError('FATAL:  database "partneros" does not exist')

    monkeypatch.setattr("app.core.database_lifecycle.create_engine", _boom)
    st, errs = check_database(
        Settings(DATABASE_URL="postgresql+psycopg://partneros:partneros@127.0.0.1:5432/partneros"),
    )
    assert st == "database_missing"
    assert any("does not exist" in e.lower() for e in errs)


def test_check_database_unavailable_refused(monkeypatch):
    def _boom(*_a, **_kw):
        raise SQLAlchemyError("connection refused")

    monkeypatch.setattr("app.core.database_lifecycle.create_engine", _boom)
    st, _ = check_database(
        Settings(DATABASE_URL="postgresql+psycopg://partneros:partneros@127.0.0.1:5432/partneros"),
    )
    assert st == "unavailable"
