"""Unit tests for quantity/unit → grams conversion and nutrient scaling."""

import pytest
from app.services.unit_conversion import quantity_to_grams, scale_nutrients


SERVING_100G = 100.0  # a product where 1 serving = 100g


class TestQuantityToGrams:
    # Absolute mass units
    def test_grams(self):
        assert quantity_to_grams(50, "g", SERVING_100G) == pytest.approx(50.0)

    def test_kilograms(self):
        assert quantity_to_grams(0.5, "kg", SERVING_100G) == pytest.approx(500.0)

    def test_ounces(self):
        assert quantity_to_grams(1, "oz", SERVING_100G) == pytest.approx(28.3495, rel=1e-3)

    def test_pounds(self):
        assert quantity_to_grams(1, "lb", SERVING_100G) == pytest.approx(453.592, rel=1e-3)

    def test_milligrams(self):
        assert quantity_to_grams(1000, "mg", SERVING_100G) == pytest.approx(1.0)

    # Volume units
    def test_cup(self):
        assert quantity_to_grams(1, "cup", SERVING_100G) == pytest.approx(240.0)

    def test_tablespoon(self):
        assert quantity_to_grams(2, "tbsp", SERVING_100G) == pytest.approx(30.0)

    def test_teaspoon(self):
        assert quantity_to_grams(3, "tsp", SERVING_100G) == pytest.approx(15.0)

    # Serving-based units
    def test_serving(self):
        assert quantity_to_grams(1, "serving", SERVING_100G) == pytest.approx(100.0)

    def test_two_servings(self):
        assert quantity_to_grams(2, "servings", SERVING_100G) == pytest.approx(200.0)

    def test_scoop(self):
        assert quantity_to_grams(2, "scoop", 31.0) == pytest.approx(62.0)

    def test_piece(self):
        assert quantity_to_grams(3, "piece", 50.0) == pytest.approx(150.0)

    def test_unknown_unit_treats_as_serving(self):
        assert quantity_to_grams(1.5, "portion", SERVING_100G) == pytest.approx(150.0)

    def test_empty_unit_is_serving(self):
        assert quantity_to_grams(1, "", SERVING_100G) == pytest.approx(100.0)

    def test_case_insensitive(self):
        assert quantity_to_grams(1, "OZ", SERVING_100G) == pytest.approx(28.3495, rel=1e-3)
        assert quantity_to_grams(1, "SCOOP", SERVING_100G) == pytest.approx(100.0)


class TestScaleNutrients:
    PRODUCT = {
        "serving_size_g": 31.0,
        "calories": 120.0,
        "protein_g": 24.0,
        "carbs_g": 3.0,
        "fat_g": 1.5,
        "sugar_g": 1.0,
        "fiber_g": 0.5,
        "sodium_mg": 130.0,
    }

    def test_one_serving(self):
        n = scale_nutrients(self.PRODUCT, 1, "serving")
        assert n["calories"] == pytest.approx(120.0, rel=1e-2)
        assert n["protein_g"] == pytest.approx(24.0, rel=1e-2)

    def test_two_scoops(self):
        n = scale_nutrients(self.PRODUCT, 2, "scoop")
        assert n["calories"] == pytest.approx(240.0, rel=1e-2)
        assert n["protein_g"] == pytest.approx(48.0, rel=1e-2)

    def test_half_serving(self):
        n = scale_nutrients(self.PRODUCT, 0.5, "serving")
        assert n["calories"] == pytest.approx(60.0, rel=1e-2)
        assert n["fat_g"] == pytest.approx(0.75, rel=1e-2)

    def test_exact_grams(self):
        # 62g = exactly 2 servings of 31g
        n = scale_nutrients(self.PRODUCT, 62, "g")
        assert n["calories"] == pytest.approx(240.0, rel=1e-2)

    def test_optional_fields_scaled(self):
        n = scale_nutrients(self.PRODUCT, 2, "serving")
        assert n["sugar_g"] == pytest.approx(2.0, rel=1e-2)
        assert n["sodium_mg"] == pytest.approx(260.0, rel=1e-2)

    def test_zero_serving_size_does_not_crash(self):
        product = {**self.PRODUCT, "serving_size_g": 0}
        n = scale_nutrients(product, 1, "serving")
        assert n["calories"] == pytest.approx(120.0, rel=1e-2)
