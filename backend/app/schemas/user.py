from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import ActivityLevel, Goal, Sex


_COMMON_PASSWORDS = {
    "password",
    "password1",
    "12345678",
    "123456789",
    "qwerty123",
    "iloveyou",
    "admin123",
    "letmein1",
    "welcome1",
    "monkey123",
    "dragon123",
    "nutritrack",
    "nutritrack123",
}


def validate_timezone_name(value: str) -> str:
    value = value.strip()
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("timezone must be a valid IANA timezone") from exc
    return value


def validate_body_report_map(value: Dict[str, str]) -> Dict[str, str]:
    if len(value) > 50:
        raise ValueError("body composition sections may contain at most 50 entries")
    cleaned: Dict[str, str] = {}
    for key, item in value.items():
        key_text = str(key).strip()
        value_text = str(item).strip()
        if not key_text:
            raise ValueError("body composition keys must not be empty")
        if len(key_text) > 80:
            raise ValueError("body composition keys must be at most 80 characters")
        if len(value_text) > 500:
            raise ValueError("body composition values must be at most 500 characters")
        cleaned[key_text] = value_text
    return cleaned


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    accept_privacy: bool = Field(default=False)

    @field_validator("accept_privacy")
    @classmethod
    def validate_privacy_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must accept the Privacy Policy to create an account")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(value) > 128:
            raise ValueError("Password must be at most 128 characters")
        if value.lower() in _COMMON_PASSWORDS:
            raise ValueError("Password is too common. Please choose a stronger password")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    authenticated: bool = True
    user: UserOut


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=4096)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(value) > 128:
            raise ValueError("Password must be at most 128 characters")
        if value.lower() in _COMMON_PASSWORDS:
            raise ValueError("Password is too common. Please choose a stronger password")
        return value


class DailyTargets(BaseModel):
    calories: float = Field(ge=0, le=20000)
    protein_g: float = Field(ge=0, le=2000)
    carbs_g: float = Field(ge=0, le=3000)
    fat_g: float = Field(ge=0, le=2000)
    sugar_g: Optional[float] = Field(default=None, ge=0, le=2000)
    fiber_g: Optional[float] = Field(default=None, ge=0, le=1000)
    sodium_mg: Optional[float] = Field(default=None, ge=0, le=50000)


class BodyCompositionReport(BaseModel):
    bwi_result: Optional[str] = Field(default=None, max_length=500)
    bio_age: Optional[str] = Field(default=None, max_length=100)
    waist_to_hip_ratio: Optional[str] = Field(default=None, max_length=100)
    summary: Dict[str, str] = Field(default_factory=dict)
    body_composition: Dict[str, str] = Field(default_factory=dict)
    segmental_analysis: Dict[str, str] = Field(default_factory=dict)

    @field_validator("summary", "body_composition", "segmental_analysis")
    @classmethod
    def validate_maps(cls, value: Dict[str, str]) -> Dict[str, str]:
        return validate_body_report_map(value)


class ProfileCreate(BaseModel):
    age: int = Field(ge=1, le=150, description="Age in years")
    sex: Sex
    weight_kg: float = Field(ge=1.0, le=500.0, description="Weight in kilograms")
    height_cm: float = Field(ge=50.0, le=300.0, description="Height in centimetres")
    activity_level: ActivityLevel
    goal: Goal
    timezone: str = Field(default="UTC", min_length=1, max_length=64)
    override_targets: Optional[DailyTargets] = None
    body_composition_report: Optional[BodyCompositionReport] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        return validate_timezone_name(value)


class ProfileUpdate(BaseModel):
    age: Optional[int] = Field(default=None, ge=1, le=150)
    sex: Optional[Sex] = None
    weight_kg: Optional[float] = Field(default=None, ge=1.0, le=500.0)
    height_cm: Optional[float] = Field(default=None, ge=50.0, le=300.0)
    activity_level: Optional[ActivityLevel] = None
    goal: Optional[Goal] = None
    timezone: Optional[str] = Field(default=None, min_length=1, max_length=64)
    override_targets: Optional[DailyTargets] = None
    body_composition_report: Optional[BodyCompositionReport] = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: Optional[str]) -> Optional[str]:
        return validate_timezone_name(value) if value is not None else None


class ProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    age: int
    sex: Sex
    weight_kg: float
    height_cm: float
    activity_level: ActivityLevel
    goal: Goal
    timezone: str
    daily_targets_json: Optional[Dict[str, Any]] = None
    calculated_targets: Optional[DailyTargets] = None
    body_composition_json: Optional[BodyCompositionReport] = None

    model_config = {"from_attributes": True}
