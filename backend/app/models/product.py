import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    serving_size_g = Column(Float, nullable=False)
    serving_quantity = Column(Float, nullable=True)
    serving_unit = Column(String, nullable=True)
    is_favorite = Column(Boolean, nullable=False, default=False)
    calories = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False, default=0.0)
    carbs_g = Column(Float, nullable=False, default=0.0)
    fat_g = Column(Float, nullable=False, default=0.0)
    sugar_g = Column(Float, nullable=True)
    fiber_g = Column(Float, nullable=True)
    sodium_mg = Column(Float, nullable=True)
    other_nutrients_json = Column(JSON, nullable=True)
    source_pdf_path = Column(String, nullable=True)
    chroma_indexed = Column(Boolean, nullable=False, default=False)  # Issue 14
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="products")
    meal_items = relationship("MealItem", back_populates="product")
