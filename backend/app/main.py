import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings, assert_production_settings
from app.core.database import engine, Base
from app.core.rate_limit import limiter
from app.api import auth, profile, products, meals
from app.api.users import router as users_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Fail fast on production settings that are unsafe for public traffic.
    assert_production_settings()

    # 2. Create upload and chroma dirs
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

    # 3. Import all models so Alembic/create_all can see them
    from app.models import User, UserProfile, Product, MealEntry, MealItem, RefreshToken  # noqa: F401
    from app.models.refresh_token import PasswordResetToken  # noqa: F401

    # NOTE: In production run `alembic upgrade head` as a pre-start step.
    # Base.metadata.create_all is kept here only for bare-metal dev convenience
    # (without Docker). It is a no-op if tables already exist.
    Base.metadata.create_all(bind=engine)

    # 4. Pre-warm the embedding model to prevent first-request hang (Issue 13)
    try:
        from app.services.embeddings import warm_up_embeddings
        warm_up_embeddings()
        logger.info("Embedding model pre-warmed successfully")
    except Exception as exc:
        logger.warning("Embedding model pre-warm failed (non-fatal): %s", exc)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="RAG-based personal nutrition dashboard API",
    version="0.1.0",
    lifespan=lifespan,
    # Disable debug mode — stack traces must not reach clients (Issue 3)
    debug=False,
)

# Attach rate-limiter state so @limiter.limit decorators work
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — origins from config (Issue 7)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(profile.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(meals.router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/health")
def health():
    """Health check — also verifies DB connectivity (Issue 40)."""
    from sqlalchemy import text
    from app.core.database import engine
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        db_status = "error"

    status_code = 200 if db_status == "ok" else 503
    return JSONResponse(
        {"status": "ok" if db_status == "ok" else "degraded", "db": db_status, "version": "0.1.0"},
        status_code=status_code,
    )
