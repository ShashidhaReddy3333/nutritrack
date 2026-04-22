"""
Tests for LLM JSON parsing robustness (Issue 10).
Verifies that _extract_json_from_text and _extract_json_array_from_text handle
all the edge cases that LLMs can produce.
"""

import pytest
from app.services.pdf_extraction import _extract_json_from_text, _extract_json_array_from_text


class TestExtractJsonFromText:
    def test_plain_json(self):
        text = '{"name": "Whey Protein", "calories": 120}'
        result = _extract_json_from_text(text)
        assert result["name"] == "Whey Protein"

    def test_json_with_backtick_fence(self):
        text = '```\n{"name": "Whey", "calories": 120}\n```'
        result = _extract_json_from_text(text)
        assert result["calories"] == 120

    def test_json_with_json_fence(self):
        text = '```json\n{"name": "Oats", "protein_g": 5}\n```'
        result = _extract_json_from_text(text)
        assert result["protein_g"] == 5

    def test_json_with_JSON_uppercase_fence(self):
        text = '```JSON\n{"name": "Oats", "calories": 150}\n```'
        result = _extract_json_from_text(text)
        assert result["calories"] == 150

    def test_json_embedded_in_text(self):
        text = 'Here is the extracted data: {"name": "Almonds", "calories": 170} — let me know if correct.'
        result = _extract_json_from_text(text)
        assert result["name"] == "Almonds"

    def test_json_with_trailing_text(self):
        text = '{"name": "Banana", "calories": 90}\n\nNote: values may vary.'
        result = _extract_json_from_text(text)
        assert result["name"] == "Banana"

    def test_invalid_json_raises(self):
        text = "I cannot provide nutritional data for this product."
        with pytest.raises(ValueError):
            _extract_json_from_text(text)


class TestExtractJsonArrayFromText:
    def test_plain_array(self):
        text = '[{"item": "banana", "quantity": 1, "unit": "piece"}]'
        result = _extract_json_array_from_text(text)
        assert len(result) == 1
        assert result[0]["item"] == "banana"

    def test_array_with_fence(self):
        text = '```json\n[{"item": "oats", "quantity": 40, "unit": "g"}]\n```'
        result = _extract_json_array_from_text(text)
        assert result[0]["unit"] == "g"

    def test_array_embedded_in_text(self):
        text = 'Parsed items: [{"item": "whey", "quantity": 1, "unit": "scoop"}] — done.'
        result = _extract_json_array_from_text(text)
        assert result[0]["item"] == "whey"

    def test_multi_item_array(self):
        text = '[{"item": "a", "quantity": 1, "unit": "g"}, {"item": "b", "quantity": 2, "unit": "oz"}]'
        result = _extract_json_array_from_text(text)
        assert len(result) == 2

    def test_invalid_array_raises(self):
        with pytest.raises(ValueError):
            _extract_json_array_from_text("no json here at all")
