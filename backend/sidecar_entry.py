"""
Desktop sidecar entrypoint (D3).

Frozen with PyInstaller; must not depend on developer shell or PYTHONPATH.
Sets APP_RUNTIME_MODE=desktop before the app package loads settings.
"""

from __future__ import annotations

import logging
import multiprocessing
import os
import sys

logger = logging.getLogger(__name__)


def _chdir_for_bundle() -> None:
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))


def main() -> None:
    _chdir_for_bundle()

    # Authoritative desktop runtime for this process (shell also injects APP_RUNTIME_MODE=desktop).
    os.environ["APP_RUNTIME_MODE"] = "desktop"

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", os.environ.get("INTELLIOFFICE_BACKEND_PORT", "17888")))

    logger.info("sidecar: APP_RUNTIME_MODE=%s HOST=%s PORT=%s", os.environ["APP_RUNTIME_MODE"], host, port)

    # Import app before uvicorn so PyInstaller traces the full FastAPI app graph.
    import app.main  # noqa: F401

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        factory=False,
        log_level=os.environ.get("UVICORN_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    logging.basicConfig(level=logging.INFO)
    main()
