"""
Shared test fixtures for NutriTrack backend.
Uses an in-memory SQLite database for isolation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# ── In-memory SQLite ──────────────────────────────────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def registered_user(client):
    """Register a test user and return their credentials."""
    email = "test@example.com"
    password = "Str0ng!Pass99"
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": password, "accept_privacy": True})
    assert resp.status_code == 201, resp.text
    return {"email": email, "password": password, "response": resp.json()}


@pytest.fixture
def auth_client(client, registered_user):
    """TestClient with auth cookies set after login."""
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert resp.status_code == 200
    # Cookies are set automatically on the TestClient session
    return client


@pytest.fixture
def sample_product_payload():
    return {
        "name": "Test Whey Protein",
        "brand": "TestBrand",
        "serving_size_g": 30.0,
        "serving_quantity": 1.0,
        "serving_unit": "scoop",
        "calories": 120.0,
        "protein_g": 24.0,
        "carbs_g": 3.0,
        "fat_g": 1.5,
        "sugar_g": 1.0,
        "fiber_g": 0.5,
        "sodium_mg": 130.0,
    }
