import asyncio
import logging
import tempfile
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut, ExtractionReview, NutrientData
from app.services.pdf_extraction import (
    PdfExtractionTimeout,
    PdfSafetyError,
    assess_confidence,
    extract_text_from_pdf_isolated,
    normalise_with_llm,
)
from app.services.embeddings import index_product, delete_product_embeddings
from app.api.deps import get_current_user

router = APIRouter(prefix="/products", tags=["products"])
logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF"


def _validate_pdf_magic(pdf_bytes: bytes) -> None:
    """Validate that uploaded bytes are actually a PDF (Issue 9)."""
    if not pdf_bytes[:4] == PDF_MAGIC:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file does not appear to be a valid PDF",
        )


async def _read_bounded_upload(file: UploadFile) -> bytes:
    total = 0
    chunk_size = 1024 * 1024
    with tempfile.SpooledTemporaryFile(max_size=chunk_size) as tmp:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > settings.MAX_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"PDF must be under {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
                )
            tmp.write(chunk)
        tmp.seek(0)
        return tmp.read()


def _index_product_safe(product: Product, user_id: str) -> bool:
    """Attempt to index product in Chroma. Returns True on success."""
    try:
        description = (
            f"{product.name} {product.brand or ''} "
            f"calories:{product.calories} protein:{product.protein_g}g "
            f"carbs:{product.carbs_g}g fat:{product.fat_g}g "
            f"serving:{product.serving_quantity or 1} {product.serving_unit or 'serving'} "
            f"grams:{product.serving_size_g}g"
        )
        index_product(
            product_id=str(product.id),
            user_id=user_id,
            product_name=product.name,
            brand=product.brand,
            raw_text=description,
            serving_size_g=product.serving_size_g,
        )
        return True
    except Exception as exc:
        logger.warning("Chroma indexing failed for product %s: %s", product.id, exc)
        return False


# ── PDF upload + extraction preview ──────────────────────────────────────────

@router.post("/extract", response_model=ExtractionReview)
@limiter.limit("5/minute")
async def extract_pdf(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Stage 1: Upload PDF → returns extracted data for user review. Nothing is saved yet."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await _read_bounded_upload(file)

    # Validate magic bytes — not just extension (Issue 9)
    _validate_pdf_magic(pdf_bytes)

    try:
        raw_text, method = await asyncio.to_thread(extract_text_from_pdf_isolated, pdf_bytes)
    except PdfExtractionTimeout:
        raise HTTPException(status_code=408, detail="PDF extraction timed out")
    except PdfSafetyError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        data = await normalise_with_llm(raw_text)
    except Exception as exc:
        # Log full details server-side, return generic message to client (Issue 28)
        logger.error("LLM extraction error for user %s: %s", current_user.id, exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="AI processing failed. Please try again or add the product manually.",
        )

    confidence = assess_confidence(data)

    extracted = NutrientData(
        serving_size_g=float(data.get("serving_size_g") or 100),
        serving_quantity=float(data["serving_quantity"]) if data.get("serving_quantity") is not None else None,
        serving_unit=str(data["serving_unit"]).strip() if data.get("serving_unit") else None,
        calories=float(data.get("calories") or 0),
        protein_g=float(data.get("protein_g") or 0),
        carbs_g=float(data.get("carbs_g") or 0),
        fat_g=float(data.get("fat_g") or 0),
        sugar_g=float(data["sugar_g"]) if data.get("sugar_g") is not None else None,
        fiber_g=float(data["fiber_g"]) if data.get("fiber_g") is not None else None,
        sodium_mg=float(data["sodium_mg"]) if data.get("sodium_mg") is not None else None,
        other_nutrients=data.get("other_nutrients"),
    )

    return ExtractionReview(
        extracted=extracted,
        raw_text_snippet=raw_text[:1000],
        confidence=confidence,
        suggested_name=data.get("name"),
        suggested_brand=data.get("brand"),
    )


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = Product(
        user_id=current_user.id,
        name=payload.name,
        brand=payload.brand,
        serving_size_g=payload.serving_size_g,
        serving_quantity=payload.serving_quantity,
        serving_unit=payload.serving_unit,
        is_favorite=payload.is_favorite,
        calories=payload.calories,
        protein_g=payload.protein_g,
        carbs_g=payload.carbs_g,
        fat_g=payload.fat_g,
        sugar_g=payload.sugar_g,
        fiber_g=payload.fiber_g,
        sodium_mg=payload.sodium_mg,
        other_nutrients_json=payload.other_nutrients_json,
        chroma_indexed=False,
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Index in Chroma and track success (Issue 14)
    indexed = _index_product_safe(product, str(current_user.id))
    if indexed:
        product.chroma_indexed = True
        db.commit()
        db.refresh(product)
    else:
        logger.warning(
            "Product %s created but NOT indexed in Chroma — AI search will not find it",
            product.id,
        )

    return ProductOut.from_orm_safe(product)


@router.get("", response_model=list[ProductOut])
def list_products(
    search: Optional[str] = Query(default=None, min_length=1, max_length=120),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Product)
        .filter(Product.user_id == current_user.id)
        .filter(Product.is_deleted == False)  # noqa: E712
    )
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((Product.name.ilike(term)) | (Product.brand.ilike(term)))
    products = query.order_by(Product.is_favorite.desc(), Product.created_at.desc()).offset(skip).limit(limit).all()
    return [ProductOut.from_orm_safe(p) for p in products]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id,
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductOut.from_orm_safe(product)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id,
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)

    # Re-index and update tracking flag
    indexed = _index_product_safe(product, str(current_user.id))
    if indexed != product.chroma_indexed:
        product.chroma_indexed = indexed
        db.commit()
        db.refresh(product)

    return ProductOut.from_orm_safe(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id,
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        delete_product_embeddings(str(product_id))
    except Exception as exc:
        logger.warning("Could not delete embeddings for product %s: %s", product_id, exc)

    product.is_deleted = True
    product.chroma_indexed = False
    db.commit()
