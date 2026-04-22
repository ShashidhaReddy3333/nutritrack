"""Unit tests for Mifflin-St Jeor BMR and target calculation logic."""

import pytest
from app.services.nutrition_calc import calculate_bmr, calculate_tdee, calculate_targets
from app.models.user import ActivityLevel, Goal, Sex


class TestBMR:
    def test_male_bmr(self):
        bmr = calculate_bmr(80, 180, 28, Sex.male)
        # 10*80 + 6.25*180 - 5*28 + 5 = 800 + 1125 - 140 + 5 = 1790
        assert bmr == pytest.approx(1790.0)

    def test_female_bmr(self):
        bmr = calculate_bmr(65, 165, 30, Sex.female)
        # 10*65 + 6.25*165 - 5*30 - 161 = 650 + 1031.25 - 150 - 161 = 1370.25
        assert bmr == pytest.approx(1370.25)

    def test_other_sex_bmr_is_average_of_male_female(self):
        male = calculate_bmr(70, 170, 25, Sex.male)
        female = calculate_bmr(70, 170, 25, Sex.female)
        other = calculate_bmr(70, 170, 25, Sex.other)
        assert other == pytest.approx((male + female) / 2)


class TestTDEE:
    def test_sedentary_multiplier(self):
        tdee = calculate_tdee(1800, ActivityLevel.sedentary)
        assert tdee == pytest.approx(1800 * 1.2)

    def test_very_active_multiplier(self):
        tdee = calculate_tdee(2000, ActivityLevel.very_active)
        assert tdee == pytest.approx(2000 * 1.725)


class TestTargets:
    def test_cut_has_lower_calories_than_maintain(self):
        maintain = calculate_targets(80, 180, 28, Sex.male, ActivityLevel.moderately_active, Goal.maintain)
        cut = calculate_targets(80, 180, 28, Sex.male, ActivityLevel.moderately_active, Goal.cut)
        assert cut.calories < maintain.calories
        assert maintain.calories - cut.calories == pytest.approx(500.0)

    def test_bulk_has_higher_calories_than_maintain(self):
        maintain = calculate_targets(80, 180, 28, Sex.male, ActivityLevel.moderately_active, Goal.maintain)
        bulk = calculate_targets(80, 180, 28, Sex.male, ActivityLevel.moderately_active, Goal.bulk)
        assert bulk.calories > maintain.calories
        assert bulk.calories - maintain.calories == pytest.approx(300.0)

    def test_macros_sum_to_total_calories(self):
        targets = calculate_targets(70, 165, 25, Sex.female, ActivityLevel.lightly_active, Goal.maintain)
        macro_calories = (
            targets.protein_g * 4 + targets.carbs_g * 4 + targets.fat_g * 9
        )
        # Allow small rounding error
        assert abs(macro_calories - targets.calories) < 5.0

    def test_cut_has_higher_protein_pct_than_bulk(self):
        cut = calculate_targets(80, 180, 28, Sex.male, ActivityLevel.moderately_active, Goal.cut)
        bulk = calculate_targets(80, 180, 28, Sex.male, ActivityLevel.moderately_active, Goal.bulk)
        cut_pct = (cut.protein_g * 4) / cut.calories
        bulk_pct = (bulk.protein_g * 4) / bulk.calories
        assert cut_pct > bulk_pct

    def test_targets_returns_daily_targets_schema(self):
        from app.schemas.user import DailyTargets
        result = calculate_targets(75, 175, 30, Sex.male, ActivityLevel.moderately_active, Goal.maintain)
        assert isinstance(result, DailyTargets)
        assert result.calories > 0
        assert result.protein_g > 0
        assert result.carbs_g > 0
        assert result.fat_g > 0
