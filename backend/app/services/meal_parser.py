"""
Meal parsing service — rule-based parser (no external LLM required).

Parses natural-language meal descriptions into structured
[{item, quantity, unit}] lists using regex and heuristics.
"""

import logging
import re

logger = logging.getLogger(__name__)
MAX_MEAL_INPUT_LENGTH = 2000

# ---------------------------------------------------------------------------
# Unit normalisation table
# ---------------------------------------------------------------------------
UNIT_MAP: dict[str, str] = {
    "grams": "g", "gram": "g", "g": "g",
    "ounces": "oz", "ounce": "oz", "oz": "oz",
    "pounds": "lb", "pound": "lb", "lb": "lb", "lbs": "lb",
    "milliliters": "ml", "milliliter": "ml", "ml": "ml",
    "liters": "l", "liter": "l", "l": "l",
    "cups": "cup", "cup": "cup",
    "tablespoons": "tbsp", "tablespoon": "tbsp", "tbsp": "tbsp", "tbs": "tbsp",
    "teaspoons": "tsp", "teaspoon": "tsp", "tsp": "tsp",
    "scoops": "scoop", "scoop": "scoop",
    "pieces": "piece", "piece": "piece", "pcs": "piece", "pc": "piece",
    "slices": "slice", "slice": "slice",
    "servings": "serving", "serving": "serving",
}

FRACTION_MAP: dict[str, float] = {
    "½": 0.5, "¼": 0.25, "¾": 0.75,
    "⅓": 1 / 3, "⅔": 2 / 3,
    "1/2": 0.5, "1/4": 0.25, "3/4": 0.75, "1/3": 1 / 3, "2/3": 2 / 3,
}

_UNIT_STR = (
    r"(?:grams?|ounces?|pounds?|lbs?|milliliters?|liters?|cups?|"
    r"tablespoons?|teaspoons?|scoops?|pieces?|slices?|servings?|"
    r"g|oz|lb|ml|l|tbs?p|tsp|pcs?|pc)"
)
_FRAC = r"(?:½|¼|¾|⅓|⅔|[0-9]+\s*/\s*[0-9]+)"
_NUMBER = r"(?:[0-9]+(?:[.,][0-9]+)?)"
_QTY = rf"(?:{_FRAC}|{_NUMBER})"

# Pattern 1: "qty unit [of] name"  e.g. "200g chicken", "2 cups rice"
_P1 = re.compile(
    rf"^(?P<qty>{_QTY})\s*(?P<unit>{_UNIT_STR})\b\s*(?:of\s+)?(?P<name>.+)",
    re.IGNORECASE,
)
# Pattern 2: "qty name"            e.g. "2 eggs", "3 bananas"
_P2 = re.compile(
    rf"^(?P<qty>{_QTY})\s+(?P<name>[a-zA-Z].+)",
    re.IGNORECASE,
)
# Pattern 3: "name qty unit"       e.g. "chicken 200g"
_P3 = re.compile(
    rf"^(?P<name>.+?)\s+(?P<qty>{_QTY})\s*(?P<unit>{_UNIT_STR})\s*$",
    re.IGNORECASE,
)

_SPLIT_RE = re.compile(r",|\band\b|\n|\+|;", re.IGNORECASE)
_STOP_WORDS = {"with", "without", "no", "some", "a", "an", "the", "small", "medium", "large"}


def sanitize_meal_input(raw_text: str) -> str:
    text = raw_text.replace("\x00", "").strip()
    return text[:MAX_MEAL_INPUT_LENGTH]


def _parse_qty(raw: str) -> float:
    raw = raw.strip()
    if raw in FRACTION_MAP:
        return FRACTION_MAP[raw]
    if " " in raw:
        parts = raw.split()
        return sum(_parse_qty(p) for p in parts)
    if "/" in raw:
        num, den = raw.split("/", 1)
        return float(num.strip()) / float(den.strip())
    return float(raw.replace(",", "."))


def _normalise_unit(raw: str) -> str:
    return UNIT_MAP.get(raw.lower().strip(), "serving")


def _clean_name(name: str) -> str:
    name = name.strip(" ,;.\n")
    words = name.split()
    while words and words[0].lower() in _STOP_WORDS:
        words = words[1:]
    return " ".join(words).strip()


def _parse_segment(segment: str) -> dict | None:
    segment = segment.strip()
    if not segment or len(segment) < 2:
        return None

    # Try pattern 1: qty unit name
    m = _P1.match(segment)
    if m:
        try:
            qty = _parse_qty(m.group("qty"))
            name = _clean_name(m.group("name"))
            if name:
                return {"item": name, "quantity": qty, "unit": _normalise_unit(m.group("unit"))}
        except (ValueError, ZeroDivisionError):
            pass

    # Try pattern 3: name qty unit
    m = _P3.match(segment)
    if m:
        try:
            qty = _parse_qty(m.group("qty"))
            name = _clean_name(m.group("name"))
            if name:
                return {"item": name, "quantity": qty, "unit": _normalise_unit(m.group("unit"))}
        except (ValueError, ZeroDivisionError):
            pass

    # Try pattern 2: qty name
    m = _P2.match(segment)
    if m:
        try:
            qty = _parse_qty(m.group("qty"))
            name = _clean_name(m.group("name"))
            if name:
                return {"item": name, "quantity": qty, "unit": "serving"}
        except (ValueError, ZeroDivisionError):
            pass

    # Fallback: 1 serving of whatever is written
    name = _clean_name(segment)
    if name and len(name) >= 2:
        return {"item": name, "quantity": 1.0, "unit": "serving"}

    return None


async def parse_meal_text(raw_text: str) -> list[dict]:
    """
    Parse a natural-language meal description into structured items.
    Returns list of {item: str, quantity: float, unit: str}.
    """
    safe_text = sanitize_meal_input(raw_text)
    segments = [s.strip() for s in _SPLIT_RE.split(safe_text) if s.strip()]

    results: list[dict] = []
    for seg in segments:
        parsed = _parse_segment(seg)
        if parsed:
            parsed["quantity"] = min(max(parsed["quantity"], 0.01), 10_000)
            results.append(parsed)

    if not results:
        raise ValueError("Could not parse any meal items from the input")

    logger.info("Rule-based meal-parse: %d items from %d chars", len(results), len(safe_text))
    return results
