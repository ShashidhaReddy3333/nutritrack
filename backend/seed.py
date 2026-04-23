"""
Seed script — run once after migrations to populate example products.
Usage: python seed.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserProfile, ActivityLevel, Goal, Sex
from app.models.product import Product

Base.metadata.create_all(bind=engine)

SEED_EMAIL = "demo@nutritrack.app"
SEED_PASSWORD = os.environ.get("SEED_DEMO_PASSWORD", "nutritrack-dev-only-change-me")

EXAMPLE_PRODUCTS = [
    {
        "name": "Optimum Nutrition Gold Standard Whey",
        "brand": "Optimum Nutrition",
        "serving_size_g": 31.0,
        "calories": 120.0,
        "protein_g": 24.0,
        "carbs_g": 3.0,
        "fat_g": 1.5,
        "sugar_g": 1.0,
        "fiber_g": 0.5,
        "sodium_mg": 130.0,
    },
    {
        "name": "Quaker Old Fashioned Oats",
        "brand": "Quaker",
        "serving_size_g": 40.0,
        "calories": 150.0,
        "protein_g": 5.0,
        "carbs_g": 27.0,
        "fat_g": 3.0,
        "sugar_g": 1.0,
        "fiber_g": 4.0,
        "sodium_mg": 0.0,
    },
    {
        "name": "Almond Butter (Natural)",
        "brand": "Justin's",
        "serving_size_g": 32.0,
        "calories": 190.0,
        "protein_g": 7.0,
        "carbs_g": 6.0,
        "fat_g": 16.0,
        "sugar_g": 2.0,
        "fiber_g": 3.0,
        "sodium_mg": 65.0,
    },
]


def run():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == SEED_EMAIL).first()
        if existing:
            print(f"Demo user already exists ({SEED_EMAIL}). Skipping seed.")
            return

        user = User(email=SEED_EMAIL, password_hash=get_password_hash(SEED_PASSWORD))
        db.add(user)
        db.flush()

        profile = UserProfile(
            user_id=user.id,
            age=28,
            sex=Sex.male,
            weight_kg=80.0,
            height_cm=180.0,
            activity_level=ActivityLevel.moderately_active,
            goal=Goal.maintain,
            timezone="UTC",
        )
        db.add(profile)
        db.flush()

        for p in EXAMPLE_PRODUCTS:
            db.add(Product(user_id=user.id, **p))

        db.commit()
        print(f"✓ Seeded demo user: {SEED_EMAIL} / {SEED_PASSWORD}")
        print(f"✓ Added {len(EXAMPLE_PRODUCTS)} example products")

    finally:
        db.close()


if __name__ == "__main__":
    run()
