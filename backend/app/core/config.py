from functools import lru_cache
from typing import Any

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.runtime_mode import AppRuntimeMode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_RUNTIME_MODE: AppRuntimeMode = AppRuntimeMode.development

    APP_NAME: str = "intellioffice"
    PUBLIC_BASE_URL: str = ""
    PORTAL_INTEGRATION_ENABLED: bool = True
    REDIS_URL: str = ""
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_PATH: str = ""

    # Empty default: without backend/.env or env DATABASE_URL, DLM reports not_configured (no silent partneros).
    DATABASE_URL: str = ""
    SECRET_KEY: str = Field(
        default="dev-secret-change-in-production",
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"),
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    UPLOAD_DIR: str = "./uploads"

    PUBLIC_ENRICHMENT_ENABLED: bool = Field(
        True,
        description="If false, POST enrichment run returns 403 (CI / air-gapped).",
    )
    ENRICHMENT_MAX_PAGES: int = 12
    ENRICHMENT_FETCH_TIMEOUT_SEC: float = 12.0
    ENRICHMENT_MAX_RESPONSE_BYTES: int = 2_000_000
    ENRICHMENT_MAX_TEXT_CHARS_PER_PAGE: int = 120_000
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str = ""
    DEFAULT_MODEL: str = "gpt-4o-mini"
    AI_PROVIDER: str = "openai"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    def model_post_init(self, __context: Any) -> None:  # noqa: ARG002
        pass


@lru_cache
def get_settings() -> Settings:
    return Settings()
