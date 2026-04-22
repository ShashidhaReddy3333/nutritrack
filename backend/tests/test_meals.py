"""
Meal CRUD tests — covers create, list, today filter, weekly totals, date boundary, delete.
"""

import pytest
from datetime import date, datetime, timezone


def create_product(auth_client, payload):
    resp = auth_client.post("/api/v1/products", json=payload)
    assert resp.status_code == 201
    return resp.json()


def create_meal(auth_client, product_id, meal_type="lunch", raw_text="Test meal", logged_at=None):
    body = {
        "meal_type": meal_type,
        "raw_text": raw_text,
        "items": [{"product_id": product_id, "quantity": 1.0, "unit": "serving"}],
    }
    if logged_at:
        body["logged_at"] = logged_at
    resp = auth_client.post("/api/v1/meals", json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def product_in_db(auth_client, sample_product_payload):
    return create_product(auth_client, sample_product_payload)


class TestCreateMealEntry:
    def test_create_meal_success(self, auth_client, product_in_db):
        resp = auth_client.post("/api/v1/meals", json={
            "meal_type": "lunch",
            "raw_text": "1 scoop whey",
            "items": [{"product_id": product_in_db["id"], "quantity": 1.0, "unit": "serving"}],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["meal_type"] == "lunch"
        assert len(data["items"]) == 1
        assert data["total_nutrients"]["calories"] > 0

    def test_create_meal_invalid_product(self, auth_client):
        resp = auth_client.post("/api/v1/meals", json={
            "meal_type": "lunch",
            "raw_text": "mystery item",
            "items": [{"product_id": "00000000-0000-0000-0000-000000000000", "quantity": 1.0, "unit": "serving"}],
        })
        assert resp.status_code == 404


class TestListMealEntries:
    def test_list_meals_empty(self, auth_client):
        resp = auth_client.get("/api/v1/meals")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_meals_with_date_filter(self, auth_client, product_in_db):
        today = date.today().isoformat()
        create_meal(auth_client, product_in_db["id"])

        resp = auth_client.get(f"/api/v1/meals?date_filter={today}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_date_filter_invalid(self, auth_client):
        resp = auth_client.get("/api/v1/meals?date_filter=not-a-date")
        assert resp.status_code == 400

    def test_list_meals_pagination(self, auth_client, product_in_db):
        for _ in range(3):
            create_meal(auth_client, product_in_db["id"])

        resp = auth_client.get("/api/v1/meals?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestDateBoundary:
    def test_meal_at_midnight_included_in_day(self, auth_client, product_in_db):
        """Meal logged at 00:00:00 must appear in that day's results (Issue 16)."""
        today = date.today()
        midnight = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=timezone.utc).isoformat()
        create_meal(auth_client, product_in_db["id"], logged_at=midnight)

        resp = auth_client.get(f"/api/v1/meals?date_filter={today.isoformat()}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_meal_at_end_of_day_included(self, auth_client, product_in_db):
        """Meal logged at 23:59:59.999 must appear in that day's results (Issue 16)."""
        today = date.today()
        end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59, 999999, tzinfo=timezone.utc).isoformat()
        create_meal(auth_client, product_in_db["id"], logged_at=end_of_day)

        resp = auth_client.get(f"/api/v1/meals?date_filter={today.isoformat()}")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestTodayMeals:
    def test_today_meals_returns_only_today(self, auth_client, product_in_db):
        create_meal(auth_client, product_in_db["id"])
        resp = auth_client.get("/api/v1/meals/today")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestWeeklyTotals:
    def test_weekly_totals_returns_7_days(self, auth_client):
        resp = auth_client.get("/api/v1/meals/weekly-totals")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 7

    def test_weekly_totals_include_nutrients(self, auth_client, product_in_db):
        create_meal(auth_client, product_in_db["id"])
        resp = auth_client.get("/api/v1/meals/weekly-totals")
        assert resp.status_code == 200
        today_key = date.today().isoformat()
        today_data = next((d for d in resp.json() if d["date"] == today_key), None)
        assert today_data is not None
        assert today_data["calories"] > 0


class TestDailyTotals:
    def test_daily_totals_empty(self, auth_client):
        resp = auth_client.get("/api/v1/meals/daily-totals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["calories"] == 0.0

    def test_daily_totals_after_meal(self, auth_client, product_in_db):
        create_meal(auth_client, product_in_db["id"])
        resp = auth_client.get("/api/v1/meals/daily-totals")
        assert resp.status_code == 200
        assert resp.json()["calories"] > 0


class TestDeleteMealEntry:
    def test_delete_meal(self, auth_client, product_in_db):
        meal = create_meal(auth_client, product_in_db["id"])
        del_resp = auth_client.delete(f"/api/v1/meals/{meal['id']}")
        assert del_resp.status_code == 204


class TestCrossUserIsolation:
    def test_user_cannot_delete_others_meal(self, client, sample_product_payload):
        """User B must not be able to delete User A's meal entry."""
        # User A
        client.post("/api/v1/auth/register", json={"email": "a2@example.com", "password": "Str0ng!Pass99", "accept_privacy": True})
        client.post("/api/v1/auth/login", json={"email": "a2@example.com", "password": "Str0ng!Pass99"})
        product_resp = client.post("/api/v1/products", json=sample_product_payload)
        product_id = product_resp.json()["id"]
        meal_resp = client.post("/api/v1/meals", json={
            "meal_type": "lunch",
            "raw_text": "test",
            "items": [{"product_id": product_id, "quantity": 1.0, "unit": "serving"}],
        })
        meal_id = meal_resp.json()["id"]

        # User B
        client.post("/api/v1/auth/register", json={"email": "b2@example.com", "password": "Str0ng!Pass99", "accept_privacy": True})
        client.post("/api/v1/auth/login", json={"email": "b2@example.com", "password": "Str0ng!Pass99"})
        del_resp = client.delete(f"/api/v1/meals/{meal_id}")
        assert del_resp.status_code == 404
