from pathlib import Path

from app.core.db_url_utils import extract_db_user_from_error, mask_database_url
from app.core.local_env_setup import init_env_from_example


def test_mask_database_url_empty():
    assert mask_database_url("") == "not configured"
    assert mask_database_url(None) == "not configured"


def test_mask_database_url_hides_password():
    u = mask_database_url("postgresql+psycopg://partneros:secret@127.0.0.1:5432/partneros")
    assert "secret" not in u
    assert "partneros" in u


def test_extract_db_user():
    assert (
        extract_db_user_from_error('FATAL: password authentication failed for user "partneros"')
        == "partneros"
    )


def test_init_env_skips_when_exists(tmp_path: Path):
    root = tmp_path / "backend"
    root.mkdir()
    (root / ".env.example").write_text("DATABASE_URL=x\n", encoding="utf-8")
    (root / ".env").write_text("keep\n", encoding="utf-8")
    result, msg = init_env_from_example(backend_root=root)
    assert result == "exists"
    assert (root / ".env").read_text(encoding="utf-8") == "keep\n"


def test_init_env_creates_from_example(tmp_path: Path):
    root = tmp_path / "backend"
    root.mkdir()
    (root / ".env.example").write_text("FOO=1\n", encoding="utf-8")
    result, msg = init_env_from_example(backend_root=root)
    assert result == "created"
    assert (root / ".env").read_text(encoding="utf-8") == "FOO=1\n"
