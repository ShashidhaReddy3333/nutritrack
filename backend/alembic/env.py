"""Alembic environment configuration.

Reads DATABASE_URL from the environment (or falls back to the app settings)
so that `alembic upgrade head` works both inside Docker and locally.
"""

from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Pull in all models so autogenerate can detect them ───────────────────────
from app.core.database import Base  # noqa: F401
import app.models  # noqa: F401 — registers User, UserProfile, Product, MealEntry, MealItem, RefreshToken

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config

# Honour Python logging config if present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ── Database URL resolution ───────────────────────────────────────────────────

def get_url() -> str:
    """Prefer DATABASE_URL env var; fall back to app settings."""
    url = os.environ.get("DATABASE_URL")
    if url:
        # SQLAlchemy 2.x requires postgresql+psycopg2:// not postgres://
        return url.replace("postgres://", "postgresql://", 1)
    from app.core.config import settings
    return settings.DATABASE_URL


# ── Offline migrations (generate SQL without a live DB) ──────────────────────

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (connect and run against a live DB) ────────────────────

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
