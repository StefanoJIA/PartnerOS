"""Shared logic for scripts/init_local_env.py (testable without subprocess)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Literal

InitResult = Literal["created", "exists", "missing_template", "error"]


def backend_root_from_here(file_or_scripts_dir: Path) -> Path:
    """scripts/ -> backend root; pass Path(__file__).resolve().parent."""
    return file_or_scripts_dir.resolve().parent


def init_env_from_example(
    *,
    backend_root: Path,
    example_name: str = ".env.example",
    target_name: str = ".env",
) -> tuple[InitResult, str]:
    """
    Copy .env.example -> .env when target is missing.

    Returns (result, human_message).
    """
    example = backend_root / example_name
    target = backend_root / target_name
    if target.is_file():
        return "exists", f"{target_name} already exists at {target}; not overwriting."
    if not example.is_file():
        return "missing_template", f"{example_name} not found at {example}"
    try:
        shutil.copy(example, target)
    except OSError as e:
        return "error", str(e)
    return "created", f"Created {target} from {example_name}"
