from functools import lru_cache
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = PROJECT_ROOT / ".local"

_FORBIDDEN_KEYS = {
    "changeme-in-production-use-a-long-random-string",
    "dev-secret-change-in-production",
    "secret",
    "changeme",
}


class Settings(BaseSettings):
    APP_NAME: str = "NutriTrack"
    DEBUG: bool = False
    APP_ENV: str = "production"  # "development" | "production" | "test"

    DATABASE_URL: str = "postgresql://nutritrack:nutritrack@localhost:5432/nutritrack"
    POSTGRES_PASSWORD: str = ""

    SECRET_KEY: str = "changeme-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "strict"

    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT_SECONDS: float = 30.0
    OLLAMA_MAX_RETRIES: int = 2

    PUBLIC_APP_URL: str = "http://localhost:5173"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@nutritrack.app"
    SMTP_USE_TLS: bool = True

    RATE_LIMIT_STORAGE_URI: str = "memory://"
    TRUSTED_PROXY_CIDRS: list[str] = [
        "127.0.0.1/32",
        "::1/128",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
    ]

    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    PDF_MAX_PAGES: int = 6
    PDF_OCR_MAX_PAGES: int = 2
    PDF_EXTRACTION_TIMEOUT_SECONDS: int = 20
    PDF_MAX_PAGE_DIMENSION_POINTS: float = 2880.0
    PDF_MAX_RENDER_PIXELS: int = 8_000_000
    PDF_OCR_SCALE: float = 1.5

    CHROMA_PERSIST_DIR: str = str(DEFAULT_DATA_DIR / "chroma")
    UPLOAD_DIR: str = str(DEFAULT_DATA_DIR / "uploads")

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", BACKEND_DIR / ".env"),
        case_sensitive=True,
        enable_decoding=False,
    )

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        env = value.strip().lower()
        if env not in {"development", "production", "test"}:
            raise ValueError("APP_ENV must be development, production, or test")
        return env

    @field_validator("CORS_ORIGINS", "TRUSTED_PROXY_CIDRS", mode="before")
    @classmethod
    def parse_string_list(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                parsed = json.loads(text)
                if not isinstance(parsed, list):
                    raise ValueError("Expected a JSON array")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in text.split(",") if item.strip()]
        return value


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def assert_safe_secret_key() -> None:
    key = settings.SECRET_KEY.strip()
    if key in _FORBIDDEN_KEYS or len(key) < 32:
        raise RuntimeError(
            "SECRET_KEY is not set to a safe value. "
            "Generate one with: openssl rand -hex 32"
        )


def _database_password_from_url(database_url: str) -> str:
    try:
        parsed = urlparse(database_url)
    except ValueError:
        return ""
    return parsed.password or ""


def _is_local_url(value: str) -> bool:
    try:
        hostname = urlparse(value).hostname or ""
    except ValueError:
        return True
    return hostname in {"localhost", "127.0.0.1", "::1"}


def assert_production_settings() -> None:
    """Fail startup on settings that are unsafe for public production traffic."""
    if settings.APP_ENV != "production":
        return

    assert_safe_secret_key()

    if not settings.COOKIE_SECURE:
        raise RuntimeError("COOKIE_SECURE must be true in production")

    if not settings.CORS_ORIGINS:
        raise RuntimeError("CORS_ORIGINS must include at least one production origin")
    if "*" in settings.CORS_ORIGINS or any(_is_local_url(origin) for origin in settings.CORS_ORIGINS):
        raise RuntimeError("CORS_ORIGINS must not include wildcard or localhost origins in production")

    db_password = settings.POSTGRES_PASSWORD or _database_password_from_url(settings.DATABASE_URL)
    if not db_password or db_password in {"nutritrack", "CHANGE_ME", "changeme", "password"}:
        raise RuntimeError("POSTGRES_PASSWORD/DATABASE_URL must use a strong non-default password in production")

    if not settings.OLLAMA_BASE_URL.strip():
        raise RuntimeError("OLLAMA_BASE_URL must be configured in production")

    if settings.RATE_LIMIT_STORAGE_URI.startswith("memory://"):
        raise RuntimeError("RATE_LIMIT_STORAGE_URI must use Redis in production")

    if not settings.PUBLIC_APP_URL or _is_local_url(settings.PUBLIC_APP_URL):
        raise RuntimeError("PUBLIC_APP_URL must be a public HTTPS URL in production")
    if not settings.PUBLIC_APP_URL.startswith("https://"):
        raise RuntimeError("PUBLIC_APP_URL must use HTTPS in production")

    if not settings.SMTP_HOST:
        raise RuntimeError("SMTP_HOST must be configured in production")
