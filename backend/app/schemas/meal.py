from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator

from app.models.meal import MealType


class ParsedItem(BaseModel):
    item: str = Field(min_length=1, max_length=160)
    quantity: float = Field(gt=0, le=10000)
    unit: str = Field(min_length=1, max_length=40)

    @field_validator("item", "unit")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class CandidateProduct(BaseModel):
    product_id: UUID
    name: str = Field(min_length=1, max_length=160)
    brand: Optional[str] = Field(default=None, max_length=160)
    score: float = Field(ge=0, le=1)
    serving_size_g: float = Field(gt=0, le=10000)
    calories_per_serving: float = Field(ge=0, le=100000)


class ResolvedNutrients(BaseModel):
    calories: float = Field(ge=0, le=100000)
    protein_g: float = Field(ge=0, le=10000)
    carbs_g: float = Field(ge=0, le=10000)
    fat_g: float = Field(ge=0, le=10000)
    sugar_g: Optional[float] = Field(default=None, ge=0, le=10000)
    fiber_g: Optional[float] = Field(default=None, ge=0, le=10000)
    sodium_mg: Optional[float] = Field(default=None, ge=0, le=1000000)


class MealItemIn(BaseModel):
    product_id: UUID
    quantity: float = Field(gt=0, le=10000)
    unit: str = Field(min_length=1, max_length=40)

    @field_validator("unit")
    @classmethod
    def strip_unit(cls, value: str) -> str:
        return value.strip()


class MealItemOut(BaseModel):
    id: UUID
    product_id: Optional[UUID] = None
    product_name: Optional[str] = Field(default=None, max_length=160)
    product_brand: Optional[str] = Field(default=None, max_length=160)
    quantity: float = Field(gt=0, le=10000)
    unit: str = Field(min_length=1, max_length=40)
    resolved_nutrients_json: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = Field(default=None, ge=0, le=1)

    model_config = {"from_attributes": True}


class MealEntryCreate(BaseModel):
    meal_type: MealType
    raw_text: str = Field(min_length=1, max_length=2000)
    items: List[MealItemIn] = Field(min_length=1, max_length=50)
    logged_at: Optional[datetime] = None

    @field_validator("raw_text")
    @classmethod
    def strip_raw_text(cls, value: str) -> str:
        return value.strip()


class MealEntryUpdate(BaseModel):
    meal_type: MealType
    raw_text: str = Field(min_length=1, max_length=2000)
    items: List[MealItemIn] = Field(min_length=1, max_length=50)
    logged_at: Optional[datetime] = None

    @field_validator("raw_text")
    @classmethod
    def strip_raw_text(cls, value: str) -> str:
        return value.strip()


class MealEntryOut(BaseModel):
    id: UUID
    user_id: UUID
    meal_type: MealType
    logged_at: datetime
    raw_text: str = Field(min_length=1, max_length=2000)
    items: List[MealItemOut] = []
    total_nutrients: Optional[ResolvedNutrients] = None

    model_config = {"from_attributes": True}


class ParseRequest(BaseModel):
    raw_text: str = Field(min_length=1, max_length=2000)

    @field_validator("raw_text")
    @classmethod
    def strip_raw_text(cls, value: str) -> str:
        return value.strip()


class ParsedItemWithCandidates(BaseModel):
    parsed: ParsedItem
    candidates: List[CandidateProduct]
    needs_confirmation: bool  # True if best score < threshold


class ParseResponse(BaseModel):
    items: List[ParsedItemWithCandidates]
