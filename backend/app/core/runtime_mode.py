"""Single source of truth for IntelliOffice application runtime modes (see docs/runtime_modes.md)."""

from enum import Enum


class AppRuntimeMode(str, Enum):
    """Values must match APP_RUNTIME_MODE environment variable (strict)."""

    development = "development"
    desktop = "desktop"
    demo = "demo"
    future_cloud = "future_cloud"
