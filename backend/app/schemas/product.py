from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class NutrientData(BaseModel):
    """Normalized nutrient schema returned by the AI extraction step."""

    serving_size_g: float = Field(gt=0, le=10_000)
    serving_quantity: Optional[float] = Field(default=None, gt=0, le=10_000)
    serving_unit: Optional[str] = Field(default=None, max_length=40)
    calories: float = Field(ge=0, le=100_000)
    protein_g: float = Field(ge=0, le=10_000)
    carbs_g: float = Field(ge=0, le=10_000)
    fat_g: float = Field(ge=0, le=10_000)
    sugar_g: Optional[float] = Field(default=None, ge=0, le=10_000)
    fiber_g: Optional[float] = Field(default=None, ge=0, le=10_000)
    sodium_mg: Optional[float] = Field(default=None, ge=0, le=1_000_000)
    other_nutrients: Optional[dict[str, Any]] = None

    @field_validator("serving_unit")
    @classmethod
    def clean_serving_unit(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("other_nutrients")
    @classmethod
    def limit_other_nutrients(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is not None and len(value) > 50:
            raise ValueError("other_nutrients may contain at most 50 entries")
        return value


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    brand: Optional[str] = Field(default=None, max_length=160)
    serving_size_g: float = Field(gt=0, le=10_000)
    serving_quantity: Optional[float] = Field(default=None, gt=0, le=10_000)
    serving_unit: Optional[str] = Field(default=None, max_length=40)
    is_favorite: bool = False
    calories: float = Field(ge=0, le=100_000)
    protein_g: float = Field(ge=0, le=10_000)
    carbs_g: float = Field(ge=0, le=10_000)
    fat_g: float = Field(ge=0, le=10_000)
    sugar_g: Optional[float] = Field(default=None, ge=0, le=10_000)
    fiber_g: Optional[float] = Field(default=None, ge=0, le=10_000)
    sodium_mg: Optional[float] = Field(default=None, ge=0, le=1_000_000)
    other_nutrients_json: Optional[dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name is required")
        return cleaned

    @field_validator("brand", "serving_unit")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("other_nutrients_json")
    @classmethod
    def limit_other_nutrients_json(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is not None and len(value) > 50:
            raise ValueError("other_nutrients_json may contain at most 50 entries")
        return value


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=160)
    brand: Optional[str] = Field(default=None, max_length=160)
    serving_size_g: Optional[float] = Field(default=None, gt=0, le=10_000)
    serving_quantity: Optional[float] = Field(default=None, gt=0, le=10_000)
    serving_unit: Optional[str] = Field(default=None, max_length=40)
    is_favorite: Optional[bool] = None
    calories: Optional[float] = Field(default=None, ge=0, le=100_000)
    protein_g: Optional[float] = Field(default=None, ge=0, le=10_000)
    carbs_g: Optional[float] = Field(default=None, ge=0, le=10_000)
    fat_g: Optional[float] = Field(default=None, ge=0, le=10_000)
    sugar_g: Optional[float] = Field(default=None, ge=0, le=10_000)
    fiber_g: Optional[float] = Field(default=None, ge=0, le=10_000)
    sodium_mg: Optional[float] = Field(default=None, ge=0, le=1_000_000)
    other_nutrients_json: Optional[dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name is required")
        return cleaned

    @field_validator("brand", "serving_unit")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class ProductOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    brand: Optional[str] = None
    serving_size_g: float
    serving_quantity: Optional[float] = None
    serving_unit: Optional[str] = None
    is_favorite: bool
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    sugar_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    other_nutrients_json: Optional[dict[str, Any]] = None
    has_source_pdf: bool = False
    chroma_indexed: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_safe(cls, product) -> "ProductOut":
        return cls(
            id=product.id,
            user_id=product.user_id,
            name=product.name,
            brand=product.brand,
            serving_size_g=product.serving_size_g,
            serving_quantity=product.serving_quantity,
            serving_unit=product.serving_unit,
            is_favorite=product.is_favorite,
            calories=product.calories,
            protein_g=product.protein_g,
            carbs_g=product.carbs_g,
            fat_g=product.fat_g,
            sugar_g=product.sugar_g,
            fiber_g=product.fiber_g,
            sodium_mg=product.sodium_mg,
            other_nutrients_json=product.other_nutrients_json,
            has_source_pdf=bool(product.source_pdf_path),
            chroma_indexed=product.chroma_indexed,
            created_at=product.created_at,
        )


class ExtractionReview(BaseModel):
    extracted: NutrientData
    raw_text_snippet: str = Field(max_length=1000)
    confidence: str = Field(pattern="^(high|medium|low)$")
    suggested_name: Optional[str] = Field(default=None, max_length=160)
    suggested_brand: Optional[str] = Field(default=None, max_length=160)
