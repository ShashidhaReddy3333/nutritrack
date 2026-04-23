"""
Profile API tests — create, get, update, validation (Issue 32).
"""

import pytest

BASE_PROFILE = {
    "age": 28,
    "sex": "male",
    "weight_kg": 80.0,
    "height_cm": 180.0,
    "activity_level": "moderately_active",
    "goal": "maintain",
}


class TestCreateProfile:
    def test_create_profile_success(self, auth_client):
        resp = auth_client.post("/api/v1/profile", json=BASE_PROFILE)
        assert resp.status_code == 201
        data = resp.json()
        assert data["age"] == 28
        assert data["timezone"] == "UTC"
        assert data["calculated_targets"] is not None

    def test_create_profile_duplicate_fails(self, auth_client):
        auth_client.post("/api/v1/profile", json=BASE_PROFILE)
        resp = auth_client.post("/api/v1/profile", json=BASE_PROFILE)
        assert resp.status_code == 400


class TestProfileValidation:
    def test_negative_age_rejected(self, auth_client):
        resp = auth_client.post("/api/v1/profile", json={**BASE_PROFILE, "age": -5})
        assert resp.status_code == 422

    def test_age_over_150_rejected(self, auth_client):
        resp = auth_client.post("/api/v1/profile", json={**BASE_PROFILE, "age": 200})
        assert resp.status_code == 422

    def test_zero_weight_rejected(self, auth_client):
        resp = auth_client.post("/api/v1/profile", json={**BASE_PROFILE, "weight_kg": 0})
        assert resp.status_code == 422

    def test_extreme_height_rejected(self, auth_client):
        resp = auth_client.post("/api/v1/profile", json={**BASE_PROFILE, "height_cm": 1.0})
        assert resp.status_code == 422


class TestGetProfile:
    def test_get_profile(self, auth_client):
        auth_client.post("/api/v1/profile", json=BASE_PROFILE)
        resp = auth_client.get("/api/v1/profile")
        assert resp.status_code == 200
        assert resp.json()["age"] == 28

    def test_get_profile_not_found(self, auth_client):
        resp = auth_client.get("/api/v1/profile")
        assert resp.status_code == 404


class TestUpdateProfile:
    def test_update_profile(self, auth_client):
        auth_client.post("/api/v1/profile", json=BASE_PROFILE)
        resp = auth_client.patch("/api/v1/profile", json={"age": 30, "timezone": "America/Toronto"})
        assert resp.status_code == 200
        assert resp.json()["age"] == 30
        assert resp.json()["timezone"] == "America/Toronto"

    def test_update_override_targets(self, auth_client):
        auth_client.post("/api/v1/profile", json=BASE_PROFILE)
        resp = auth_client.patch(
            "/api/v1/profile",
            json={"override_targets": {"calories": 2400, "protein_g": 150, "carbs_g": 250, "fat_g": 70}},
        )
        assert resp.status_code == 200
        assert resp.json()["daily_targets_json"]["calories"] == 2400

    def test_clear_override_targets_with_null(self, auth_client):
        auth_client.post("/api/v1/profile", json={
            **BASE_PROFILE,
            "override_targets": {"calories": 2500, "protein_g": 160, "carbs_g": 300, "fat_g": 80},
        })
        resp = auth_client.patch("/api/v1/profile", json={"override_targets": None})
        assert resp.status_code == 200
        assert resp.json()["daily_targets_json"] is None
