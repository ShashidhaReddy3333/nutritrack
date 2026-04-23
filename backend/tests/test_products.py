"""
Product CRUD tests — covers create, list, get, update, delete, pagination.
"""

import pytest


class TestCreateProduct:
    def test_create_product_success(self, auth_client, sample_product_payload):
        resp = auth_client.post("/api/v1/products", json=sample_product_payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == sample_product_payload["name"]
        assert data["calories"] == sample_product_payload["calories"]
        # source_pdf_path must NOT be in the response (Issue 18)
        assert "source_pdf_path" not in data
        # has_source_pdf bool should be present instead
        assert "has_source_pdf" in data

    def test_create_product_unauthenticated(self, client, sample_product_payload):
        resp = client.post("/api/v1/products", json=sample_product_payload)
        assert resp.status_code == 401


class TestListProducts:
    def test_list_products_empty(self, auth_client):
        resp = auth_client.get("/api/v1/products")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_products_with_items(self, auth_client, sample_product_payload):
        auth_client.post("/api/v1/products", json=sample_product_payload)
        resp = auth_client.get("/api/v1/products")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_products_pagination(self, auth_client, sample_product_payload):
        # Create 3 products
        for i in range(3):
            payload = {**sample_product_payload, "name": f"Product {i}"}
            auth_client.post("/api/v1/products", json=payload)

        resp = auth_client.get("/api/v1/products?limit=2&skip=0")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        resp2 = auth_client.get("/api/v1/products?limit=2&skip=2")
        assert resp2.status_code == 200
        assert len(resp2.json()) == 1

    def test_list_products_search(self, auth_client, sample_product_payload):
        auth_client.post("/api/v1/products", json={**sample_product_payload, "name": "Greek Yogurt"})
        auth_client.post("/api/v1/products", json={**sample_product_payload, "name": "Almond Butter"})

        resp = auth_client.get("/api/v1/products?search=yogurt")
        assert resp.status_code == 200
        assert [item["name"] for item in resp.json()] == ["Greek Yogurt"]

    def test_products_isolated_between_users(self, client, sample_product_payload):
        """User A cannot see User B's products."""
        # Register user A
        client.post("/api/v1/auth/register", json={"email": "a@example.com", "password": "Str0ng!Pass99", "accept_privacy": True})
        client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "Str0ng!Pass99"})
        client.post("/api/v1/products", json=sample_product_payload)

        # Register user B
        client.post("/api/v1/auth/register", json={"email": "b@example.com", "password": "Str0ng!Pass99", "accept_privacy": True})
        client.post("/api/v1/auth/login", json={"email": "b@example.com", "password": "Str0ng!Pass99"})
        resp = client.get("/api/v1/products")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetProduct:
    def test_get_product(self, auth_client, sample_product_payload):
        create_resp = auth_client.post("/api/v1/products", json=sample_product_payload)
        product_id = create_resp.json()["id"]

        resp = auth_client.get(f"/api/v1/products/{product_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == product_id

    def test_get_nonexistent_product(self, auth_client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = auth_client.get(f"/api/v1/products/{fake_id}")
        assert resp.status_code == 404


class TestUpdateProduct:
    def test_update_product(self, auth_client, sample_product_payload):
        create_resp = auth_client.post("/api/v1/products", json=sample_product_payload)
        product_id = create_resp.json()["id"]

        resp = auth_client.patch(f"/api/v1/products/{product_id}", json={"calories": 200.0})
        assert resp.status_code == 200
        assert resp.json()["calories"] == 200.0

    def test_update_product_allows_clearing_optional_fields(self, auth_client, sample_product_payload):
        create_resp = auth_client.post("/api/v1/products", json=sample_product_payload)
        product_id = create_resp.json()["id"]

        resp = auth_client.patch(f"/api/v1/products/{product_id}", json={"brand": None, "sugar_g": None})
        assert resp.status_code == 200
        assert resp.json()["brand"] is None
        assert resp.json()["sugar_g"] is None


class TestDeleteProduct:
    def test_delete_product(self, auth_client, sample_product_payload):
        create_resp = auth_client.post("/api/v1/products", json=sample_product_payload)
        product_id = create_resp.json()["id"]

        del_resp = auth_client.delete(f"/api/v1/products/{product_id}")
        assert del_resp.status_code == 204

        get_resp = auth_client.get(f"/api/v1/products/{product_id}")
        assert get_resp.status_code == 404


class TestPDFMagicBytes:
    def test_non_pdf_file_rejected(self, auth_client):
        """File with wrong magic bytes should be rejected even with .pdf extension (Issue 9)."""
        fake_pdf_bytes = b"This is not a PDF file at all"
        resp = auth_client.post(
            "/api/v1/products/extract",
            files={"file": ("fake.pdf", fake_pdf_bytes, "application/pdf")},
        )
        assert resp.status_code == 400
        assert "valid PDF" in resp.json()["detail"]
