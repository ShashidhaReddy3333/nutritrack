import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class MealType(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


class MealEntry(Base):
    __tablename__ = "meal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    meal_type = Column(Enum(MealType), nullable=False)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    raw_text = Column(String, nullable=False)
    parsed_items_json = Column(JSON, nullable=True)

    user = relationship("User", back_populates="meal_entries")
    items = relationship("MealItem", back_populates="meal_entry", cascade="all, delete-orphan")


class MealItem(Base):
    __tablename__ = "meal_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_entry_id = Column(UUID(as_uuid=True), ForeignKey("meal_entries.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    product_name_snapshot = Column(String, nullable=True)
    product_brand_snapshot = Column(String, nullable=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    resolved_nutrients_json = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)

    meal_entry = relationship("MealEntry", back_populates="items")
    product = relationship("Product", back_populates="meal_items")
