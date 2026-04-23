import pytest

from app.core import config
from app.core.config import Settings


def production_settings(**overrides):
    values = {
        "APP_ENV": "production",
        "SECRET_KEY": "a" * 64,
        "DATABASE_URL": "postgresql://nutritrack:strong-db-password@db:5432/nutritrack",
        "POSTGRES_PASSWORD": "strong-db-password",
        "CORS_ORIGINS": ["https://nutritrack.example"],
        "COOKIE_SECURE": True,
        "PUBLIC_APP_URL": "https://nutritrack.example",
        "SMTP_HOST": "smtp.example",
        "SMTP_FROM": "no-reply@nutritrack.example",
        "OLLAMA_BASE_URL": "https://llm.example/v1",
        "RATE_LIMIT_STORAGE_URI": "redis://redis:6379/0",
    }
    values.update(overrides)
    return Settings(**values)


def test_cors_origins_accept_comma_separated_string():
    settings = Settings(APP_ENV="test", CORS_ORIGINS="https://a.example, https://b.example")
    assert settings.CORS_ORIGINS == ["https://a.example", "https://b.example"]


def test_production_rejects_weak_secret(monkeypatch):
    monkeypatch.setattr(config, "settings", production_settings(SECRET_KEY="dev-secret-change-in-production"))
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        config.assert_production_settings()


def test_production_rejects_default_database_password(monkeypatch):
    monkeypatch.setattr(
        config,
        "settings",
        production_settings(
            POSTGRES_PASSWORD="nutritrack",
            DATABASE_URL="postgresql://nutritrack:nutritrack@db:5432/nutritrack",
        ),
    )
    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        config.assert_production_settings()


def test_production_accepts_hardened_required_settings(monkeypatch):
    monkeypatch.setattr(config, "settings", production_settings())
    config.assert_production_settings()
