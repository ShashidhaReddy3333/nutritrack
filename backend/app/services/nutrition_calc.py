"""
Nutrition calculation service.

BMR via Mifflin-St Jeor equation:
  Male:   10 * weight_kg + 6.25 * height_cm - 5 * age + 5
  Female: 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
  Other:  average of male and female

TDEE = BMR * activity_multiplier

Macro splits by goal:
  maintain: protein 30%, carbs 40%, fat 30%
  cut:      protein 40%, carbs 30%, fat 30%
  bulk:     protein 25%, carbs 50%, fat 25%
"""

from app.models.user import ActivityLevel, Goal, Sex
from app.schemas.user import DailyTargets

ACTIVITY_MULTIPLIERS = {
    ActivityLevel.sedentary: 1.2,
    ActivityLevel.lightly_active: 1.375,
    ActivityLevel.moderately_active: 1.55,
    ActivityLevel.very_active: 1.725,
    ActivityLevel.extra_active: 1.9,
}

GOAL_ADJUSTMENTS = {
    Goal.maintain: 0,
    Goal.cut: -500,
    Goal.bulk: +300,
}

MACRO_SPLITS = {
    # (protein_pct, carbs_pct, fat_pct)
    Goal.maintain: (0.30, 0.40, 0.30),
    Goal.cut: (0.40, 0.30, 0.30),
    Goal.bulk: (0.25, 0.50, 0.25),
}

CALORIES_PER_GRAM = {"protein": 4.0, "carbs": 4.0, "fat": 9.0}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: Sex) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex == Sex.male:
        return base + 5
    elif sex == Sex.female:
        return base - 161
    else:
        # average
        return base - 78


def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
    return bmr * ACTIVITY_MULTIPLIERS[activity_level]


def calculate_targets(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: Sex,
    activity_level: ActivityLevel,
    goal: Goal,
) -> DailyTargets:
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)
    calories = tdee + GOAL_ADJUSTMENTS[goal]

    protein_pct, carbs_pct, fat_pct = MACRO_SPLITS[goal]
    protein_g = (calories * protein_pct) / CALORIES_PER_GRAM["protein"]
    carbs_g = (calories * carbs_pct) / CALORIES_PER_GRAM["carbs"]
    fat_g = (calories * fat_pct) / CALORIES_PER_GRAM["fat"]

    # Reasonable default micros
    fiber_g = 25.0 if sex != Sex.male else 38.0
    sodium_mg = 2300.0
    sugar_g = calories * 0.05 / 4.0  # <5% of calories from added sugar

    return DailyTargets(
        calories=round(calories, 1),
        protein_g=round(protein_g, 1),
        carbs_g=round(carbs_g, 1),
        fat_g=round(fat_g, 1),
        fiber_g=round(fiber_g, 1),
        sodium_mg=round(sodium_mg, 1),
        sugar_g=round(sugar_g, 1),
    )
