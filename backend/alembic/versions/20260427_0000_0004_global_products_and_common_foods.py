"""Add is_global to products, create system user, seed 100 common foods.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-27
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone
import uuid

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

# Fixed UUID for the system/global user
SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000001"

# 100 most common foods with accurate nutritional data (per 100g unless noted)
COMMON_FOODS = [
    # ── Proteins ────────────────────────────────────────────────────────────
    {"name": "Chicken Breast", "brand": "Common Foods", "serving_size_g": 100, "serving_quantity": 100, "serving_unit": "g",
     "calories": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6, "sodium_mg": 74},
    {"name": "Chicken Thigh", "brand": "Common Foods", "serving_size_g": 100, "serving_quantity": 100, "serving_unit": "g",
     "calories": 209, "protein_g": 26, "carbs_g": 0, "fat_g": 11, "sodium_mg": 84},
    {"name": "Ground Beef (80% lean)", "brand": "Common Foods", "serving_size_g": 100, "serving_quantity": 100, "serving_unit": "g",
     "calories": 254, "protein_g": 17, "carbs_g": 0, "fat_g": 20, "sodium_mg": 72},
    {"name": "Salmon Fillet", "brand": "Common Foods", "serving_size_g": 100, "serving_quantity": 100, "serving_unit": "g",
     "calories": 208, "protein_g": 20, "carbs_g": 0, "fat_g": 13, "sodium_mg": 59},
    {"name": "Tuna (Canned in Water)", "brand": "Common Foods", "serving_size_g": 100, "serving_quantity": 100, "serving_unit": "g",
     "calories": 116, "protein_g": 26, "carbs_g": 0, "fat_g": 1, "sodium_mg": 337},
    {"name": "Shrimp", "brand": "Common Foods", "serving_size_g": 100, "serving_quantity": 100, "serving_unit": "g",
     "calories": 99, "protein_g": 24, "carbs_g": 0, "fat_g": 0.3, "sodium_mg": 111},
    {"name": "Turkey Breast", "brand": "Common Foods", "serving_size_g": 100, "serving_quantity": 100, "serving_unit": "g",
     "calories": 135, "protein_g": 30, "carbs_g": 0, "fat_g": 1, "sodium_mg": 63},
    {"name": "Pork Tenderloin", "brand": "Common Foods", "serving_size_g": 100, "serving_quantity": 100, "serving_unit": "g",
     "calories": 143, "protein_g": 26, "carbs_g": 0, "fat_g": 3.5, "sodium_mg": 58},
    {"name": "Tofu (Firm)", "brand": "Common Foods", "serving_size_g": 100, "serving_quantity": 100, "serving_unit": "g",
     "calories": 76, "protein_g": 8, "carbs_g": 1.9, "fat_g": 4.8, "sodium_mg": 7},
    {"name": "Eggs (Whole)", "brand": "Common Foods", "serving_size_g": 50, "serving_quantity": 1, "serving_unit": "egg",
     "calories": 72, "protein_g": 6.3, "carbs_g": 0.4, "fat_g": 5, "sodium_mg": 71},
    {"name": "Egg White", "brand": "Common Foods", "serving_size_g": 33, "serving_quantity": 1, "serving_unit": "egg white",
     "calories": 17, "protein_g": 3.6, "carbs_g": 0.2, "fat_g": 0.1, "sodium_mg": 55},
    # ── Dairy ────────────────────────────────────────────────────────────────
    {"name": "Whole Milk", "brand": "Common Foods", "serving_size_g": 244, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 149, "protein_g": 8, "carbs_g": 12, "fat_g": 8, "sodium_mg": 105},
    {"name": "Skim Milk", "brand": "Common Foods", "serving_size_g": 244, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 83, "protein_g": 8, "carbs_g": 12, "fat_g": 0.2, "sodium_mg": 103},
    {"name": "Greek Yogurt (Plain, 0%)", "brand": "Common Foods", "serving_size_g": 170, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 100, "protein_g": 17, "carbs_g": 6, "fat_g": 0.7, "sodium_mg": 60},
    {"name": "Cottage Cheese (Low-fat)", "brand": "Common Foods", "serving_size_g": 113, "serving_quantity": 0.5, "serving_unit": "cup",
     "calories": 90, "protein_g": 12, "carbs_g": 5, "fat_g": 2.5, "sodium_mg": 360},
    {"name": "Cheddar Cheese", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "oz",
     "calories": 113, "protein_g": 7, "carbs_g": 0.4, "fat_g": 9, "sodium_mg": 174},
    {"name": "Mozzarella Cheese", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "oz",
     "calories": 85, "protein_g": 6.3, "carbs_g": 0.6, "fat_g": 6.3, "sodium_mg": 138},
    {"name": "Butter", "brand": "Common Foods", "serving_size_g": 14, "serving_quantity": 1, "serving_unit": "tbsp",
     "calories": 100, "protein_g": 0.1, "carbs_g": 0, "fat_g": 11, "sodium_mg": 90},
    # ── Grains & Starches ────────────────────────────────────────────────────
    {"name": "White Rice (Cooked)", "brand": "Common Foods", "serving_size_g": 186, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 242, "protein_g": 4.4, "carbs_g": 53, "fat_g": 0.4, "fiber_g": 0.6, "sodium_mg": 2},
    {"name": "Brown Rice (Cooked)", "brand": "Common Foods", "serving_size_g": 195, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 216, "protein_g": 5, "carbs_g": 45, "fat_g": 1.8, "fiber_g": 3.5, "sodium_mg": 10},
    {"name": "Oats (Dry)", "brand": "Common Foods", "serving_size_g": 40, "serving_quantity": 0.5, "serving_unit": "cup",
     "calories": 150, "protein_g": 5, "carbs_g": 27, "fat_g": 3, "fiber_g": 4, "sodium_mg": 0},
    {"name": "Whole Wheat Bread", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "slice",
     "calories": 69, "protein_g": 3.6, "carbs_g": 12, "fat_g": 1, "fiber_g": 1.9, "sodium_mg": 132},
    {"name": "White Bread", "brand": "Common Foods", "serving_size_g": 25, "serving_quantity": 1, "serving_unit": "slice",
     "calories": 67, "protein_g": 2, "carbs_g": 12.7, "fat_g": 0.8, "fiber_g": 0.6, "sodium_mg": 131},
    {"name": "Pasta (Cooked)", "brand": "Common Foods", "serving_size_g": 140, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 220, "protein_g": 8, "carbs_g": 43, "fat_g": 1.3, "fiber_g": 2.5, "sodium_mg": 1},
    {"name": "Quinoa (Cooked)", "brand": "Common Foods", "serving_size_g": 185, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 222, "protein_g": 8, "carbs_g": 39, "fat_g": 3.6, "fiber_g": 5, "sodium_mg": 13},
    {"name": "Sweet Potato (Baked)", "brand": "Common Foods", "serving_size_g": 130, "serving_quantity": 1, "serving_unit": "medium",
     "calories": 112, "protein_g": 2, "carbs_g": 26, "fat_g": 0.1, "fiber_g": 3.8, "sodium_mg": 72},
    {"name": "White Potato (Baked)", "brand": "Common Foods", "serving_size_g": 173, "serving_quantity": 1, "serving_unit": "medium",
     "calories": 161, "protein_g": 4.3, "carbs_g": 37, "fat_g": 0.2, "fiber_g": 3.8, "sodium_mg": 17},
    {"name": "Tortilla (Flour)", "brand": "Common Foods", "serving_size_g": 45, "serving_quantity": 1, "serving_unit": "piece",
     "calories": 146, "protein_g": 3.8, "carbs_g": 25, "fat_g": 3.5, "fiber_g": 1.7, "sodium_mg": 217},
    # ── Fruits ───────────────────────────────────────────────────────────────
    {"name": "Banana", "brand": "Common Foods", "serving_size_g": 118, "serving_quantity": 1, "serving_unit": "medium",
     "calories": 105, "protein_g": 1.3, "carbs_g": 27, "fat_g": 0.4, "fiber_g": 3.1, "sugar_g": 14},
    {"name": "Apple", "brand": "Common Foods", "serving_size_g": 182, "serving_quantity": 1, "serving_unit": "medium",
     "calories": 95, "protein_g": 0.5, "carbs_g": 25, "fat_g": 0.3, "fiber_g": 4.4, "sugar_g": 19},
    {"name": "Orange", "brand": "Common Foods", "serving_size_g": 131, "serving_quantity": 1, "serving_unit": "medium",
     "calories": 62, "protein_g": 1.2, "carbs_g": 15, "fat_g": 0.2, "fiber_g": 3.1, "sugar_g": 12},
    {"name": "Blueberries", "brand": "Common Foods", "serving_size_g": 148, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 84, "protein_g": 1.1, "carbs_g": 21, "fat_g": 0.5, "fiber_g": 3.6, "sugar_g": 15},
    {"name": "Strawberries", "brand": "Common Foods", "serving_size_g": 152, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 49, "protein_g": 1, "carbs_g": 12, "fat_g": 0.5, "fiber_g": 3, "sugar_g": 7},
    {"name": "Avocado", "brand": "Common Foods", "serving_size_g": 201, "serving_quantity": 1, "serving_unit": "medium",
     "calories": 322, "protein_g": 4, "carbs_g": 17, "fat_g": 29, "fiber_g": 13, "sugar_g": 1.3},
    {"name": "Grapes", "brand": "Common Foods", "serving_size_g": 92, "serving_quantity": 0.5, "serving_unit": "cup",
     "calories": 62, "protein_g": 0.6, "carbs_g": 16, "fat_g": 0.2, "fiber_g": 0.8, "sugar_g": 13},
    {"name": "Watermelon", "brand": "Common Foods", "serving_size_g": 280, "serving_quantity": 2, "serving_unit": "cup",
     "calories": 85, "protein_g": 1.7, "carbs_g": 21, "fat_g": 0.4, "fiber_g": 1.1, "sugar_g": 18},
    {"name": "Mango", "brand": "Common Foods", "serving_size_g": 165, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 99, "protein_g": 1.4, "carbs_g": 25, "fat_g": 0.6, "fiber_g": 2.6, "sugar_g": 22.5},
    # ── Vegetables ──────────────────────────────────────────────────────────
    {"name": "Broccoli", "brand": "Common Foods", "serving_size_g": 91, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 31, "protein_g": 2.6, "carbs_g": 6, "fat_g": 0.3, "fiber_g": 2.4, "sodium_mg": 30},
    {"name": "Spinach (Raw)", "brand": "Common Foods", "serving_size_g": 30, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 7, "protein_g": 0.9, "carbs_g": 1.1, "fat_g": 0.1, "fiber_g": 0.7, "sodium_mg": 24},
    {"name": "Kale (Raw)", "brand": "Common Foods", "serving_size_g": 67, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 34, "protein_g": 2.2, "carbs_g": 6.7, "fat_g": 0.5, "fiber_g": 1.3, "sodium_mg": 29},
    {"name": "Carrots", "brand": "Common Foods", "serving_size_g": 128, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 52, "protein_g": 1.2, "carbs_g": 12, "fat_g": 0.3, "fiber_g": 3.6, "sodium_mg": 88},
    {"name": "Bell Pepper (Red)", "brand": "Common Foods", "serving_size_g": 92, "serving_quantity": 0.5, "serving_unit": "cup",
     "calories": 23, "protein_g": 0.9, "carbs_g": 4.5, "fat_g": 0.3, "fiber_g": 1.5, "sodium_mg": 3},
    {"name": "Cucumber", "brand": "Common Foods", "serving_size_g": 119, "serving_quantity": 0.5, "serving_unit": "cup",
     "calories": 16, "protein_g": 0.7, "carbs_g": 3.8, "fat_g": 0.1, "fiber_g": 0.5, "sodium_mg": 2},
    {"name": "Tomato", "brand": "Common Foods", "serving_size_g": 123, "serving_quantity": 1, "serving_unit": "medium",
     "calories": 22, "protein_g": 1.1, "carbs_g": 4.8, "fat_g": 0.2, "fiber_g": 1.5, "sodium_mg": 6},
    {"name": "Onion", "brand": "Common Foods", "serving_size_g": 148, "serving_quantity": 1, "serving_unit": "medium",
     "calories": 60, "protein_g": 1.7, "carbs_g": 14, "fat_g": 0.1, "fiber_g": 2.6, "sodium_mg": 6},
    {"name": "Garlic", "brand": "Common Foods", "serving_size_g": 4, "serving_quantity": 1, "serving_unit": "clove",
     "calories": 5, "protein_g": 0.2, "carbs_g": 1, "fat_g": 0, "fiber_g": 0.1, "sodium_mg": 1},
    {"name": "Zucchini", "brand": "Common Foods", "serving_size_g": 124, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 21, "protein_g": 1.5, "carbs_g": 3.9, "fat_g": 0.4, "fiber_g": 1.2, "sodium_mg": 10},
    {"name": "Asparagus", "brand": "Common Foods", "serving_size_g": 134, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 27, "protein_g": 3, "carbs_g": 5, "fat_g": 0.2, "fiber_g": 2.8, "sodium_mg": 3},
    {"name": "Green Beans", "brand": "Common Foods", "serving_size_g": 110, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 35, "protein_g": 2, "carbs_g": 8, "fat_g": 0.1, "fiber_g": 3.4, "sodium_mg": 7},
    {"name": "Corn (Cooked)", "brand": "Common Foods", "serving_size_g": 154, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 143, "protein_g": 5.4, "carbs_g": 31, "fat_g": 2, "fiber_g": 3.6, "sodium_mg": 28},
    {"name": "Mushrooms", "brand": "Common Foods", "serving_size_g": 70, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 15, "protein_g": 2.2, "carbs_g": 2.3, "fat_g": 0.2, "fiber_g": 0.7, "sodium_mg": 4},
    {"name": "Celery", "brand": "Common Foods", "serving_size_g": 101, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 16, "protein_g": 0.7, "carbs_g": 3, "fat_g": 0.2, "fiber_g": 1.6, "sodium_mg": 81},
    # ── Legumes & Beans ──────────────────────────────────────────────────────
    {"name": "Black Beans (Cooked)", "brand": "Common Foods", "serving_size_g": 172, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 227, "protein_g": 15, "carbs_g": 41, "fat_g": 0.9, "fiber_g": 15, "sodium_mg": 2},
    {"name": "Chickpeas (Cooked)", "brand": "Common Foods", "serving_size_g": 164, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 269, "protein_g": 15, "carbs_g": 45, "fat_g": 4.2, "fiber_g": 12.5, "sodium_mg": 11},
    {"name": "Lentils (Cooked)", "brand": "Common Foods", "serving_size_g": 198, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 230, "protein_g": 18, "carbs_g": 40, "fat_g": 0.8, "fiber_g": 16, "sodium_mg": 4},
    {"name": "Edamame", "brand": "Common Foods", "serving_size_g": 155, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 189, "protein_g": 17, "carbs_g": 15, "fat_g": 8, "fiber_g": 8, "sodium_mg": 9},
    # ── Nuts & Seeds ─────────────────────────────────────────────────────────
    {"name": "Almonds", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "oz",
     "calories": 164, "protein_g": 6, "carbs_g": 6.1, "fat_g": 14, "fiber_g": 3.5, "sodium_mg": 0},
    {"name": "Peanuts", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "oz",
     "calories": 161, "protein_g": 7.3, "carbs_g": 4.6, "fat_g": 14, "fiber_g": 2.4, "sodium_mg": 5},
    {"name": "Walnuts", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "oz",
     "calories": 185, "protein_g": 4.3, "carbs_g": 3.9, "fat_g": 18.5, "fiber_g": 1.9, "sodium_mg": 1},
    {"name": "Cashews", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "oz",
     "calories": 157, "protein_g": 5.2, "carbs_g": 8.6, "fat_g": 12.4, "fiber_g": 0.9, "sodium_mg": 3},
    {"name": "Peanut Butter", "brand": "Common Foods", "serving_size_g": 32, "serving_quantity": 2, "serving_unit": "tbsp",
     "calories": 188, "protein_g": 8, "carbs_g": 6.9, "fat_g": 16, "fiber_g": 1.9, "sodium_mg": 147},
    {"name": "Almond Butter", "brand": "Common Foods", "serving_size_g": 32, "serving_quantity": 2, "serving_unit": "tbsp",
     "calories": 196, "protein_g": 6.7, "carbs_g": 6, "fat_g": 18.3, "fiber_g": 1.6, "sodium_mg": 4},
    {"name": "Chia Seeds", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 2, "serving_unit": "tbsp",
     "calories": 138, "protein_g": 4.7, "carbs_g": 12, "fat_g": 8.7, "fiber_g": 9.8, "sodium_mg": 5},
    {"name": "Flaxseeds", "brand": "Common Foods", "serving_size_g": 14, "serving_quantity": 1, "serving_unit": "tbsp",
     "calories": 55, "protein_g": 1.9, "carbs_g": 3, "fat_g": 4.3, "fiber_g": 2.8, "sodium_mg": 3},
    {"name": "Sunflower Seeds", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "oz",
     "calories": 165, "protein_g": 5.5, "carbs_g": 6.5, "fat_g": 14.4, "fiber_g": 2.4, "sodium_mg": 1},
    # ── Oils & Fats ──────────────────────────────────────────────────────────
    {"name": "Olive Oil", "brand": "Common Foods", "serving_size_g": 14, "serving_quantity": 1, "serving_unit": "tbsp",
     "calories": 119, "protein_g": 0, "carbs_g": 0, "fat_g": 13.5, "sodium_mg": 0},
    {"name": "Coconut Oil", "brand": "Common Foods", "serving_size_g": 14, "serving_quantity": 1, "serving_unit": "tbsp",
     "calories": 121, "protein_g": 0, "carbs_g": 0, "fat_g": 13.5, "sodium_mg": 0},
    {"name": "Vegetable Oil", "brand": "Common Foods", "serving_size_g": 14, "serving_quantity": 1, "serving_unit": "tbsp",
     "calories": 120, "protein_g": 0, "carbs_g": 0, "fat_g": 13.6, "sodium_mg": 0},
    # ── Beverages ────────────────────────────────────────────────────────────
    {"name": "Orange Juice", "brand": "Common Foods", "serving_size_g": 248, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 112, "protein_g": 1.7, "carbs_g": 26, "fat_g": 0.5, "sugar_g": 21, "sodium_mg": 2},
    {"name": "Black Coffee", "brand": "Common Foods", "serving_size_g": 237, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 2, "protein_g": 0.3, "carbs_g": 0, "fat_g": 0, "sodium_mg": 5},
    {"name": "Green Tea", "brand": "Common Foods", "serving_size_g": 237, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 2, "protein_g": 0, "carbs_g": 0.5, "fat_g": 0, "sodium_mg": 2},
    # ── Protein Supplements ──────────────────────────────────────────────────
    {"name": "Whey Protein Powder", "brand": "Common Foods", "serving_size_g": 30, "serving_quantity": 1, "serving_unit": "scoop",
     "calories": 120, "protein_g": 24, "carbs_g": 3, "fat_g": 1.5, "sodium_mg": 130},
    {"name": "Casein Protein Powder", "brand": "Common Foods", "serving_size_g": 34, "serving_quantity": 1, "serving_unit": "scoop",
     "calories": 120, "protein_g": 24, "carbs_g": 4, "fat_g": 1, "sodium_mg": 220},
    {"name": "Plant Protein Powder", "brand": "Common Foods", "serving_size_g": 30, "serving_quantity": 1, "serving_unit": "scoop",
     "calories": 110, "protein_g": 20, "carbs_g": 5, "fat_g": 2, "fiber_g": 2, "sodium_mg": 250},
    # ── Common Meals & Snacks ────────────────────────────────────────────────
    {"name": "Hummus", "brand": "Common Foods", "serving_size_g": 60, "serving_quantity": 0.25, "serving_unit": "cup",
     "calories": 108, "protein_g": 5, "carbs_g": 12, "fat_g": 5, "fiber_g": 3.8, "sodium_mg": 214},
    {"name": "Granola Bar", "brand": "Common Foods", "serving_size_g": 47, "serving_quantity": 1, "serving_unit": "bar",
     "calories": 193, "protein_g": 4, "carbs_g": 29, "fat_g": 7.6, "fiber_g": 2.4, "sugar_g": 12, "sodium_mg": 95},
    {"name": "Dark Chocolate (70%)", "brand": "Common Foods", "serving_size_g": 40, "serving_quantity": 1.5, "serving_unit": "oz",
     "calories": 216, "protein_g": 2.9, "carbs_g": 17.7, "fat_g": 15, "fiber_g": 4, "sugar_g": 8},
    {"name": "Rice Cakes", "brand": "Common Foods", "serving_size_g": 18, "serving_quantity": 2, "serving_unit": "piece",
     "calories": 70, "protein_g": 1.4, "carbs_g": 15, "fat_g": 0.6, "fiber_g": 0.4, "sodium_mg": 30},
    {"name": "Protein Bar", "brand": "Common Foods", "serving_size_g": 60, "serving_quantity": 1, "serving_unit": "bar",
     "calories": 200, "protein_g": 20, "carbs_g": 22, "fat_g": 6, "fiber_g": 3, "sugar_g": 5, "sodium_mg": 150},
    {"name": "Mixed Nuts", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "oz",
     "calories": 168, "protein_g": 5, "carbs_g": 7.2, "fat_g": 14.6, "fiber_g": 1.8, "sodium_mg": 55},
    {"name": "Popcorn (Air-Popped)", "brand": "Common Foods", "serving_size_g": 8, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 31, "protein_g": 1, "carbs_g": 6.2, "fat_g": 0.4, "fiber_g": 1.2, "sodium_mg": 1},
    # ── Condiments & Sauces ──────────────────────────────────────────────────
    {"name": "Ketchup", "brand": "Common Foods", "serving_size_g": 17, "serving_quantity": 1, "serving_unit": "tbsp",
     "calories": 20, "protein_g": 0.3, "carbs_g": 4.8, "fat_g": 0, "sugar_g": 4.1, "sodium_mg": 160},
    {"name": "Mustard", "brand": "Common Foods", "serving_size_g": 5, "serving_quantity": 1, "serving_unit": "tsp",
     "calories": 3, "protein_g": 0.2, "carbs_g": 0.3, "fat_g": 0.2, "sodium_mg": 57},
    {"name": "Mayonnaise", "brand": "Common Foods", "serving_size_g": 15, "serving_quantity": 1, "serving_unit": "tbsp",
     "calories": 94, "protein_g": 0.1, "carbs_g": 0.1, "fat_g": 10.3, "sodium_mg": 88},
    {"name": "Soy Sauce", "brand": "Common Foods", "serving_size_g": 16, "serving_quantity": 1, "serving_unit": "tbsp",
     "calories": 8, "protein_g": 1.3, "carbs_g": 0.8, "fat_g": 0.1, "sodium_mg": 879},
    {"name": "Hot Sauce", "brand": "Common Foods", "serving_size_g": 5, "serving_quantity": 1, "serving_unit": "tsp",
     "calories": 1, "protein_g": 0.1, "carbs_g": 0.1, "fat_g": 0, "sodium_mg": 124},
    {"name": "Honey", "brand": "Common Foods", "serving_size_g": 21, "serving_quantity": 1, "serving_unit": "tbsp",
     "calories": 64, "protein_g": 0.1, "carbs_g": 17.3, "fat_g": 0, "sugar_g": 17.2, "sodium_mg": 1},
    {"name": "Salsa", "brand": "Common Foods", "serving_size_g": 64, "serving_quantity": 0.25, "serving_unit": "cup",
     "calories": 18, "protein_g": 1, "carbs_g": 3.7, "fat_g": 0.2, "fiber_g": 1, "sodium_mg": 360},
    # ── Breakfast Items ──────────────────────────────────────────────────────
    {"name": "Bacon (Cooked)", "brand": "Common Foods", "serving_size_g": 19, "serving_quantity": 2, "serving_unit": "slice",
     "calories": 87, "protein_g": 5.9, "carbs_g": 0.1, "fat_g": 6.8, "sodium_mg": 367},
    {"name": "Pancake (Plain)", "brand": "Common Foods", "serving_size_g": 77, "serving_quantity": 1, "serving_unit": "piece",
     "calories": 175, "protein_g": 5, "carbs_g": 22, "fat_g": 7.4, "fiber_g": 0.8, "sodium_mg": 388},
    {"name": "Cereal (Corn Flakes)", "brand": "Common Foods", "serving_size_g": 28, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 101, "protein_g": 2, "carbs_g": 24, "fat_g": 0.2, "fiber_g": 1, "sugar_g": 2.4, "sodium_mg": 203},
    # ── Soups & Mixed Dishes ─────────────────────────────────────────────────
    {"name": "Chicken Noodle Soup", "brand": "Common Foods", "serving_size_g": 245, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 75, "protein_g": 5, "carbs_g": 9, "fat_g": 2.5, "fiber_g": 0.7, "sodium_mg": 866},
    {"name": "Tomato Soup", "brand": "Common Foods", "serving_size_g": 245, "serving_quantity": 1, "serving_unit": "cup",
     "calories": 88, "protein_g": 1.7, "carbs_g": 17, "fat_g": 2.7, "fiber_g": 1, "sodium_mg": 932},
]


def upgrade() -> None:
    # 1. Add is_global column
    op.add_column(
        "products",
        sa.Column("is_global", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_products_is_global", "products", ["is_global"])

    # 2. Create system user (used as owner of all global products)
    op.execute(
        sa.text("""
            INSERT INTO users (id, email, password_hash, created_at)
            VALUES (
                CAST(:id AS uuid), :email, :password_hash, :created_at
            )
            ON CONFLICT (id) DO NOTHING
        """).bindparams(
            id=SYSTEM_USER_ID,
            email="system@nutritrack.internal",
            password_hash="!disabled",
            created_at=datetime.now(timezone.utc),
        )
    )

    # 3. Seed 100 common foods
    now = datetime.now(timezone.utc)
    for food in COMMON_FOODS:
        op.execute(
            sa.text("""
                INSERT INTO products (
                    id, user_id, name, brand,
                    serving_size_g, serving_quantity, serving_unit,
                    is_favorite, calories, protein_g, carbs_g, fat_g,
                    sugar_g, fiber_g, sodium_mg,
                    is_global, chroma_indexed, is_deleted, created_at
                ) VALUES (
                    CAST(:id AS uuid), CAST(:user_id AS uuid), :name, :brand,
                    :serving_size_g, :serving_quantity, :serving_unit,
                    false, :calories, :protein_g, :carbs_g, :fat_g,
                    :sugar_g, :fiber_g, :sodium_mg,
                    true, false, false, :created_at
                )
                ON CONFLICT (id) DO NOTHING
            """).bindparams(
                id=str(uuid.uuid5(uuid.UUID(SYSTEM_USER_ID), food["name"])),
                user_id=SYSTEM_USER_ID,
                name=food["name"],
                brand=food.get("brand"),
                serving_size_g=food["serving_size_g"],
                serving_quantity=food.get("serving_quantity"),
                serving_unit=food.get("serving_unit"),
                calories=food["calories"],
                protein_g=food["protein_g"],
                carbs_g=food["carbs_g"],
                fat_g=food["fat_g"],
                sugar_g=food.get("sugar_g"),
                fiber_g=food.get("fiber_g"),
                sodium_mg=food.get("sodium_mg"),
                created_at=now,
            )
        )


def downgrade() -> None:
    # Remove seeded global products and system user
    op.execute(
        sa.text("DELETE FROM products WHERE is_global = true AND user_id = CAST(:uid AS uuid)").bindparams(
            uid=SYSTEM_USER_ID
        )
    )
    op.execute(
        sa.text("DELETE FROM users WHERE id = CAST(:uid AS uuid)").bindparams(uid=SYSTEM_USER_ID)
    )
    op.drop_index("ix_products_is_global", table_name="products")
    op.drop_column("products", "is_global")
