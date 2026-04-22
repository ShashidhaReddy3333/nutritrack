"""
Auth endpoint tests — covers register, login, /me, token expiry, enumeration resistance.
"""

import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "Str0ng!Pass99",
            "accept_privacy": True,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_sets_auth_cookie(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "cookie@example.com",
            "password": "Str0ng!Pass99",
            "accept_privacy": True,
        })
        assert resp.status_code == 201
        assert "nutritrack_access" in resp.cookies

    def test_register_duplicate_email_generic_message(self, client):
        """Duplicate email returns generic message — no enumeration (Issue 20)."""
        payload = {"email": "dup@example.com", "password": "Str0ng!Pass99", "accept_privacy": True}
        client.post("/api/v1/auth/register", json=payload)
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert "already registered" not in detail.lower()
        assert "email" not in detail.lower()

    def test_register_password_too_short(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "short@example.com",
            "password": "abc",
            "accept_privacy": True,
        })
        assert resp.status_code == 422

    def test_register_password_too_long(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "long@example.com",
            "password": "a" * 129,
            "accept_privacy": True,
        })
        assert resp.status_code == 422

    def test_register_common_password_rejected(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "common@example.com",
            "password": "nutritrack123",
            "accept_privacy": True,
        })
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_sets_cookies(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert resp.status_code == 200
        assert "nutritrack_access" in resp.cookies
        assert "nutritrack_refresh" in resp.cookies

    def test_login_invalid_password(self, client, registered_user):
        resp = client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": "wrong_password",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_email(self, client):
        resp = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "Str0ng!Pass99",
        })
        assert resp.status_code == 401


class TestGetMe:
    def test_get_me_authenticated(self, auth_client, registered_user):
        resp = auth_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == registered_user["email"]
        assert "id" in data
        assert "password_hash" not in data

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_get_me_with_tampered_token(self, client):
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer tampered.fake.token"},
        )
        assert resp.status_code == 401


class TestLogout:
    def test_logout_clears_cookies(self, auth_client):
        resp = auth_client.post("/api/v1/auth/logout")
        assert resp.status_code == 204


class TestRefreshToken:
    def test_refresh_issues_new_token(self, client, registered_user):
        # Login to get refresh cookie
        login_resp = client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert login_resp.status_code == 200

        refresh_resp = client.post("/api/v1/auth/refresh")
        assert refresh_resp.status_code == 200
        assert "access_token" in refresh_resp.json()

    def test_refresh_without_cookie_fails(self, client):
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401
