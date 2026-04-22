"""
Unit normalisation: convert any quantity+unit to grams relative to a product's serving_size_g.

Supports: g, kg, oz, lb, mg, ml, l, serving(s), scoop(s), cup, tbsp, tsp, piece(s), slice(s).
"""

UNIT_TO_GRAMS: dict[str, float] = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "kilograms": 1000.0,
    "oz": 28.3495,
    "ounce": 28.3495,
    "ounces": 28.3495,
    "lb": 453.592,
    "lbs": 453.592,
    "pound": 453.592,
    "pounds": 453.592,
    "mg": 0.001,
    "milligram": 0.001,
    "milligrams": 0.001,
    # Volume — approximate water density (1 g/ml)
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,
    "millilitre": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "liters": 1000.0,
    "litre": 1000.0,
    "cup": 240.0,
    "cups": 240.0,
    "tbsp": 15.0,
    "tablespoon": 15.0,
    "tablespoons": 15.0,
    "tsp": 5.0,
    "teaspoon": 5.0,
    "teaspoons": 5.0,
    "fl oz": 29.574,
    "fluid oz": 29.574,
}

SERVING_UNITS = {"serving", "servings", "scoop", "scoops", "piece", "pieces", "slice", "slices", "unit", "units"}


def _normalise_unit(unit: str) -> str:
    return unit.lower().strip()


def _unit_variants(unit: str) -> set[str]:
    base = _normalise_unit(unit)
    if not base:
        return {""}

    variants = {base}
    if base.endswith("y") and len(base) > 1:
        variants.add(f"{base[:-1]}ies")
    elif base.endswith(("s", "x", "z", "ch", "sh")):
        variants.add(f"{base}es")
    else:
        variants.add(f"{base}s")

    if base.endswith("es") and len(base) > 2:
        variants.add(base[:-2])
    if base.endswith("s") and len(base) > 1:
        variants.add(base[:-1])

    return variants


def quantity_to_grams(
    quantity: float,
    unit: str,
    serving_size_g: float,
    serving_quantity: float | None = None,
    serving_unit: str | None = None,
) -> float:
    """
    Convert quantity+unit to grams.
    If unit is a serving-type, multiply quantity by serving_size_g.
    If unit is an absolute mass/volume unit, convert to grams directly.
    Falls back to treating unknown units as servings.
    """
    unit_lower = _normalise_unit(unit)

    if serving_unit and serving_quantity and serving_quantity > 0:
        if unit_lower in _unit_variants(serving_unit):
            return (quantity / serving_quantity) * serving_size_g

    if unit_lower in SERVING_UNITS or unit_lower == "":
        return quantity * serving_size_g

    gram_factor = UNIT_TO_GRAMS.get(unit_lower)
    if gram_factor:
        return quantity * gram_factor

    # Unknown unit → treat as serving
    return quantity * serving_size_g


def scale_nutrients(
    product: dict,
    quantity: float,
    unit: str,
) -> dict:
    """
    Scale a product's nutrient values by (quantity_grams / serving_size_g).
    product dict must have: serving_size_g, calories, protein_g, carbs_g, fat_g,
    and optionally sugar_g, fiber_g, sodium_mg.
    """
    serving_size_g = product["serving_size_g"]
    quantity_grams = quantity_to_grams(
        quantity,
        unit,
        serving_size_g,
        product.get("serving_quantity"),
        product.get("serving_unit"),
    )
    factor = quantity_grams / serving_size_g if serving_size_g > 0 else 1.0

    result: dict = {
        "calories": round(product.get("calories", 0) * factor, 1),
        "protein_g": round(product.get("protein_g", 0) * factor, 2),
        "carbs_g": round(product.get("carbs_g", 0) * factor, 2),
        "fat_g": round(product.get("fat_g", 0) * factor, 2),
    }
    for optional in ("sugar_g", "fiber_g", "sodium_mg"):
        val = product.get(optional)
        if val is not None:
            result[optional] = round(val * factor, 2)

    return result
