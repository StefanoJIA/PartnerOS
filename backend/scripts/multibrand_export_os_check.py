"""Multibrand export OS readiness gate."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic.config import Config
from alembic.script import ScriptDirectory


def main() -> int:
    cfg = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    head = ScriptDirectory.from_config(cfg).get_current_head()
    expected = "0031_platform_intelligence"
    ok = head == expected
    print(f"Migration head: {head} (expected {expected})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
