"""
User management endpoints — account deletion & data export (GDPR / CCPA compliance).
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserProfile
from app.models.product import Product
from app.models.meal import MealEntry
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete the authenticated user's account and all associated data.
    GDPR Article 17 — Right to erasure.
    """
    from app.services.embeddings import delete_product_embeddings

    # Remove product embeddings from Chroma
    products = db.query(Product).filter(Product.user_id == current_user.id).all()
    for product in products:
        try:
            delete_product_embeddings(str(product.id))
        except Exception as exc:
            logger.warning("Could not delete Chroma embeddings for product %s: %s", product.id, exc)

    db.delete(current_user)  # cascades to profile, products, meal_entries, refresh_tokens
    db.commit()

    # Clear auth cookies
    from app.api.auth import _clear_auth_cookies
    _clear_auth_cookies(response)
    logger.info("Account deleted for user %s", current_user.id)


@router.get("/me/export")
def export_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export all user data as JSON.
    GDPR Article 20 — Right to data portability.
    """
    profile = current_user.profile

    products = db.query(Product).filter(Product.user_id == current_user.id).all()
    meals = db.query(MealEntry).filter(MealEntry.user_id == current_user.id).all()

    export = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "profile": {
            "age": profile.age if profile else None,
            "sex": profile.sex.value if profile else None,
            "weight_kg": profile.weight_kg if profile else None,
            "height_cm": profile.height_cm if profile else None,
            "activity_level": profile.activity_level.value if profile else None,
            "goal": profile.goal.value if profile else None,
            "timezone": profile.timezone if profile else None,
            "daily_targets_json": profile.daily_targets_json if profile else None,
            "body_composition_json": profile.body_composition_json if profile else None,
        } if profile else None,
        "products": [
            {
                "id": str(p.id),
                "name": p.name,
                "brand": p.brand,
                "serving_size_g": p.serving_size_g,
                "calories": p.calories,
                "protein_g": p.protein_g,
                "carbs_g": p.carbs_g,
                "fat_g": p.fat_g,
                "sugar_g": p.sugar_g,
                "fiber_g": p.fiber_g,
                "sodium_mg": p.sodium_mg,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in products
        ],
        "meal_entries": [
            {
                "id": str(m.id),
                "meal_type": m.meal_type.value,
                "logged_at": m.logged_at.isoformat() if m.logged_at else None,
                "raw_text": m.raw_text,
                "items": [
                    {
                        "product_id": str(i.product_id) if i.product_id else None,
                        "quantity": i.quantity,
                        "unit": i.unit,
                        "nutrients": i.resolved_nutrients_json,
                    }
                    for i in m.items
                ],
            }
            for m in meals
        ],
    }

    return JSONResponse(
        content=export,
        headers={
            "Content-Disposition": f'attachment; filename="nutritrack_export_{datetime.now(timezone.utc).strftime("%Y%m%d")}.json"',
            "Content-Type": "application/json",
        },
    )
