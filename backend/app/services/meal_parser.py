"""
Meal parsing service.

One Ollama call:
1. Parse natural language → [{item, quantity, unit}]
2. (skipped — RAG retrieval does product matching)
"""

import logging
import time

from openai import AsyncOpenAI
from app.core.config import settings
from app.services.pdf_extraction import _extract_json_array_from_text

logger = logging.getLogger(__name__)
MAX_MEAL_INPUT_LENGTH = 2000

PARSE_SYSTEM = """\
You are a meal log parser. Given a natural-language meal description, extract every distinct \
food item and its quantity/unit.

Return ONLY a JSON array — no explanation, no markdown fences. Each element:
{"item": <string>, "quantity": <number>, "unit": <string>}

Unit should be one of: g, oz, lb, ml, l, cup, tbsp, tsp, serving, scoop, piece, slice.
If no explicit quantity is given, assume 1 serving.
Examples:
Input: "2 scoops whey protein, 1 medium banana, black coffee"
Output: [{"item":"whey protein","quantity":2,"unit":"scoop"},{"item":"banana","quantity":1,"unit":"piece"},{"item":"black coffee","quantity":240,"unit":"ml"}]
"""


def sanitize_meal_input(raw_text: str) -> str:
    text = raw_text.replace("\x00", "").strip()
    text = text[:MAX_MEAL_INPUT_LENGTH]
    return text


def _validate_parsed_items(items: list) -> list[dict]:
    allowed_units = {"g", "oz", "lb", "ml", "l", "cup", "tbsp", "tsp", "serving", "scoop", "piece", "slice"}
    validated: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("item", "")).strip()[:120]
        if not name:
            continue
        try:
            quantity = float(item.get("quantity", 1))
        except (TypeError, ValueError):
            quantity = 1.0
        unit = str(item.get("unit", "serving")).strip().lower()
        if unit not in allowed_units:
            unit = "serving"
        validated.append({"item": name, "quantity": max(quantity, 0.01), "unit": unit})
    if not validated:
        raise ValueError("LLM returned no valid meal items")
    return validated


async def parse_meal_text(raw_text: str) -> list[dict]:
    """Returns list of {item, quantity, unit} dicts using local Llama via Ollama."""
    client = AsyncOpenAI(base_url=settings.OLLAMA_BASE_URL, api_key="ollama", timeout=settings.OLLAMA_TIMEOUT_SECONDS)
    safe_text = sanitize_meal_input(raw_text)
    start = time.time()

    max_retries = max(settings.OLLAMA_MAX_RETRIES, 1)
    last_exc = None
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=settings.OLLAMA_MODEL,
                max_tokens=512,
                messages=[
                    {"role": "system", "content": PARSE_SYSTEM},
                    {"role": "user", "content": safe_text},
                ],
            )
            latency_ms = int((time.time() - start) * 1000)
            response_text = (response.choices[0].message.content or "").strip()
            logger.info("Ollama meal-parse | model=%s | latency_ms=%d", settings.OLLAMA_MODEL, latency_ms)
            logger.debug("Ollama parse response: %s", response_text)
            return _validate_parsed_items(_extract_json_array_from_text(response_text))
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                logger.warning("Meal parse attempt %d failed, retrying: %s", attempt + 1, exc)

    raise ValueError(f"Failed to parse meal text after {max_retries} attempts: {last_exc}")
