import pytest
from pydantic import ValidationError

from app.schemas.meal import MealItemIn, ParseRequest
from app.schemas.product import ProductCreate
from app.schemas.user import DailyTargets, ProfileCreate


def test_product_rejects_negative_nutrients(sample_product_payload):
    with pytest.raises(ValidationError):
        ProductCreate(**{**sample_product_payload, "calories": -1})


def test_meal_rejects_negative_quantity():
    with pytest.raises(ValidationError):
        MealItemIn(product_id="00000000-0000-0000-0000-000000000000", quantity=-1, unit="serving")


def test_parse_request_rejects_huge_raw_text():
    with pytest.raises(ValidationError):
        ParseRequest(raw_text="x" * 2001)


def test_daily_targets_reject_extreme_values():
    with pytest.raises(ValidationError):
        DailyTargets(calories=50000, protein_g=100, carbs_g=100, fat_g=100)


def test_profile_rejects_invalid_timezone():
    with pytest.raises(ValidationError):
        ProfileCreate(
            age=30,
            sex="male",
            weight_kg=80,
            height_cm=180,
            activity_level="moderately_active",
            goal="maintain",
            timezone="Not/AZone",
        )
