"""
PDF extraction service.

Fallback chain:
  1. pdfplumber  — best for text PDFs with tables
  2. PyMuPDF     — good for text-heavy PDFs
  3. pytesseract — last resort OCR for scanned images

Then the local Ollama model normalises the raw text into the NutrientData JSON schema.
"""

import io
import json
import logging
import multiprocessing as mp
import queue
import re
import time
from typing import Optional

from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)
MAX_LABEL_INPUT_LENGTH = 8000


class PdfSafetyError(ValueError):
    """Raised when a PDF violates processing safety limits."""


class PdfExtractionTimeout(TimeoutError):
    """Raised when PDF extraction exceeds the configured timeout."""


def validate_pdf_limits(pdf_bytes: bytes) -> None:
    try:
        import fitz

        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            if doc.is_encrypted or doc.needs_pass:
                raise PdfSafetyError("Encrypted PDFs are not supported")
            if doc.page_count > settings.PDF_MAX_PAGES:
                raise PdfSafetyError(f"PDF must contain at most {settings.PDF_MAX_PAGES} pages")
            for page_number, page in enumerate(doc, start=1):
                rect = page.rect
                if (
                    rect.width > settings.PDF_MAX_PAGE_DIMENSION_POINTS
                    or rect.height > settings.PDF_MAX_PAGE_DIMENSION_POINTS
                ):
                    raise PdfSafetyError(f"PDF page {page_number} is too large to process safely")
    except PdfSafetyError:
        raise
    except Exception as exc:
        raise PdfSafetyError("Could not validate PDF structure") from exc

# ── Text extraction helpers ───────────────────────────────────────────────────

def _extract_with_pdfplumber(pdf_bytes: bytes) -> Optional[str]:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            text_parts.append(" | ".join(str(c or "") for c in row))
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        result = "\n".join(text_parts).strip()
        return result if len(result) > 50 else None
    except Exception as exc:
        logger.warning("pdfplumber failed: %s", exc)
        return None


def _extract_with_pymupdf(pdf_bytes: bytes) -> Optional[str]:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = [page.get_text() for page in doc]
        doc.close()
        result = "\n".join(text_parts).strip()
        return result if len(result) > 50 else None
    except Exception as exc:
        logger.warning("PyMuPDF failed: %s", exc)
        return None


def _extract_with_ocr(pdf_bytes: bytes) -> Optional[str]:
    try:
        import fitz
        from PIL import Image
        import pytesseract

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        for page_number, page in enumerate(doc, start=1):
            if page_number > settings.PDF_OCR_MAX_PAGES:
                break
            mat = fitz.Matrix(settings.PDF_OCR_SCALE, settings.PDF_OCR_SCALE)
            pix = page.get_pixmap(matrix=mat)
            if pix.width * pix.height > settings.PDF_MAX_RENDER_PIXELS:
                raise PdfSafetyError("PDF page render size is too large to OCR safely")
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text_parts.append(pytesseract.image_to_string(img))
        doc.close()
        result = "\n".join(text_parts).strip()
        return result if len(result) > 50 else None
    except PdfSafetyError:
        raise
    except Exception as exc:
        logger.warning("OCR failed: %s", exc)
        return None


def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, str]:
    """
    Returns (text, method_used).
    Raises ValueError if all methods fail.
    """
    validate_pdf_limits(pdf_bytes)
    for method, fn in [
        ("pdfplumber", _extract_with_pdfplumber),
        ("pymupdf", _extract_with_pymupdf),
        ("ocr", _extract_with_ocr),
    ]:
        text = fn(pdf_bytes)
        if text:
            logger.info("PDF extracted via %s (%d chars)", method, len(text))
            return text, method

    raise ValueError(
        "Could not extract text from PDF. "
        "The file may be corrupt, password-protected, or contain only images that OCR could not read."
    )


def _pdf_extraction_worker(pdf_bytes: bytes, result_queue) -> None:
    try:
        text, method = extract_text_from_pdf(pdf_bytes)
        result_queue.put(("ok", text, method))
    except Exception as exc:
        result_queue.put(("error", exc.__class__.__name__, str(exc)))


def extract_text_from_pdf_isolated(pdf_bytes: bytes) -> tuple[str, str]:
    """Extract PDF text in a separate process with a hard timeout."""
    validate_pdf_limits(pdf_bytes)
    ctx = mp.get_context("spawn")
    result_queue = ctx.Queue(maxsize=1)
    process = ctx.Process(target=_pdf_extraction_worker, args=(pdf_bytes, result_queue))
    process.start()
    process.join(settings.PDF_EXTRACTION_TIMEOUT_SECONDS)
    if process.is_alive():
        process.terminate()
        process.join(2)
        raise PdfExtractionTimeout("PDF extraction timed out")

    try:
        result = result_queue.get_nowait()
    except queue.Empty as exc:
        raise ValueError("PDF extraction failed") from exc

    status = result[0]
    if status == "ok":
        return result[1], result[2]
    error_type, message = result[1], result[2]
    if error_type == "PdfSafetyError":
        raise PdfSafetyError(message)
    raise ValueError(message or "PDF extraction failed")


# ── Robust JSON extraction ────────────────────────────────────────────────────

def _extract_json_from_text(text: str) -> dict:
    """
    Robustly extract a JSON object from LLM output (Issue 10).

    Strategy:
    1. Try direct json.loads()
    2. Strip markdown code fences and retry
    3. Use regex to find the first JSON object in the text
    """
    text = text.strip()

    # 1. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown fences (handles ```json, ```JSON, ```, etc.)
    fence_pattern = re.compile(r"^```(?:json|JSON)?\s*\n?(.*?)\n?```", re.DOTALL)
    fence_match = fence_pattern.search(text)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Regex: find the first {...} block in the text
    object_match = re.search(r"\{.*\}", text, re.DOTALL)
    if object_match:
        try:
            return json.loads(object_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]!r}")


def _extract_json_array_from_text(text: str) -> list:
    """Robustly extract a JSON array from LLM output (Issue 10)."""
    text = text.strip()

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    fence_pattern = re.compile(r"^```(?:json|JSON)?\s*\n?(.*?)\n?```", re.DOTALL)
    fence_match = fence_pattern.search(text)
    if fence_match:
        try:
            result = json.loads(fence_match.group(1).strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    array_match = re.search(r"\[.*\]", text, re.DOTALL)
    if array_match:
        try:
            result = json.loads(array_match.group(0))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON array from LLM response: {text[:200]!r}")


# ── Ollama normalisation ──────────────────────────────────────────────────────

EXTRACTION_SYSTEM = """\
You are a nutrition label parser. Extract nutritional information from the provided text \
and return ONLY a valid JSON object — no explanation, no markdown fences.

Required fields (use null if genuinely absent):
{
  "name": string,
  "brand": string | null,
  "serving_size_g": number,
  "calories": number,
  "protein_g": number,
  "carbs_g": number,
  "fat_g": number,
  "sugar_g": number | null,
  "fiber_g": number | null,
  "sodium_mg": number | null,
  "other_nutrients": {}
}

Unit conversion rules:
- Convert oz → g (* 28.35), lb → g (* 453.6)
- Convert mg protein/carbs/fat → g (/ 1000) if clearly milligrams
- Sodium always in mg; if given in g multiply by 1000
- If serving size given as "1 scoop (31g)" extract 31
"""

EXTRACTION_PROMPT = """\
Extract nutritional data from the following product label text:

---
{text}
---

Return ONLY the JSON object.
"""


def sanitize_label_text(raw_text: str) -> str:
    return raw_text.replace("\x00", "").strip()[:MAX_LABEL_INPUT_LENGTH]


def _validate_nutrient_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("LLM response was not a JSON object")
    for field in ("serving_size_g", "calories", "protein_g", "carbs_g", "fat_g"):
        try:
            data[field] = float(data.get(field) or 0)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid numeric field: {field}")
        if data[field] < 0:
            raise ValueError(f"Negative numeric field: {field}")
    data["name"] = str(data.get("name") or "").strip()[:160]
    if not data["name"]:
        data["name"] = "Imported product"
    if data.get("brand") is not None:
        data["brand"] = str(data["brand"]).strip()[:160] or None
    return data


async def normalise_with_llm(raw_text: str) -> dict:
    """
    Call local Llama via Ollama to parse raw PDF text into structured nutrition JSON.

    Normalises label text with the configured local LLM.
    """
    client = AsyncOpenAI(base_url=settings.OLLAMA_BASE_URL, api_key="ollama", timeout=settings.OLLAMA_TIMEOUT_SECONDS)

    prompt = EXTRACTION_PROMPT.format(text=sanitize_label_text(raw_text))
    start = time.time()
    max_retries = max(settings.OLLAMA_MAX_RETRIES, 1)
    last_exc = None
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=settings.OLLAMA_MODEL,
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            latency_ms = int((time.time() - start) * 1000)
            response_text = (response.choices[0].message.content or "").strip()
            logger.info("Ollama extraction | model=%s | latency_ms=%d", settings.OLLAMA_MODEL, latency_ms)
            logger.debug("Ollama extraction response: %s", response_text)
            return _validate_nutrient_payload(_extract_json_from_text(response_text))
        except (ValueError, json.JSONDecodeError, Exception) as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                logger.warning("Extraction attempt %d failed, retrying: %s", attempt + 1, exc)

    raise ValueError(f"Failed to parse LLM nutrition response after {max_retries} attempts: {last_exc}")


# ── backward-compat alias ──────────────────────────────────────────────────────
# ── Confidence heuristic ──────────────────────────────────────────────────────

def assess_confidence(data: dict) -> str:
    required = ["calories", "protein_g", "carbs_g", "fat_g", "serving_size_g"]
    if all(isinstance(data.get(k), (int, float)) and data[k] >= 0 for k in required):
        if data.get("sodium_mg") is not None and data.get("sugar_g") is not None:
            return "high"
        return "medium"
    return "low"
