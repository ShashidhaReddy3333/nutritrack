"""
User management tests — account deletion, data export (GDPR, Issue 29).
"""


class TestDataExport:
    def test_export_data_returns_json(self, auth_client):
        resp = auth_client.get("/api/v1/users/me/export")
        assert resp.status_code == 200
        data = resp.json()
        assert "user" in data
        assert "products" in data
        assert "meal_entries" in data
        assert "exported_at" in data

    def test_export_data_unauthenticated(self, client):
        resp = client.get("/api/v1/users/me/export")
        assert resp.status_code == 401


class TestDeleteAccount:
    def test_delete_account(self, auth_client, registered_user):
        resp = auth_client.delete("/api/v1/users/me")
        assert resp.status_code == 204

    def test_deleted_account_cannot_login(self, client, registered_user):
        # Login with the auth_client
        client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        # Delete
        client.delete("/api/v1/users/me")
        # Try to login again — should fail
        resp = client.post("/api/v1/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert resp.status_code == 401
