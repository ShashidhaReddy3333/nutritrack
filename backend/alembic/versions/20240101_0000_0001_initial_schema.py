"""Initial schema — full database setup.

Creates all tables in their hardened form:
  - users, user_profiles (with enums)
  - products (with serving_quantity, serving_unit, is_favorite, chroma_indexed)
  - meal_entries, meal_items
  - refresh_tokens (Issue 6 / 8 — refresh token rotation)

Revision ID: 0001
Revises: None
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum types ────────────────────────────────────────────────────────────
    sex_enum = postgresql.ENUM("male", "female", "other", name="sex")
    activity_enum = postgresql.ENUM(
        "sedentary", "lightly_active", "moderately_active", "very_active", "extra_active",
        name="activitylevel",
    )
    goal_enum = postgresql.ENUM("maintain", "cut", "bulk", name="goal")
    meal_type_enum = postgresql.ENUM("breakfast", "lunch", "dinner", "snack", name="mealtype")

    sex_enum.create(op.get_bind(), checkfirst=True)
    activity_enum.create(op.get_bind(), checkfirst=True)
    goal_enum.create(op.get_bind(), checkfirst=True)
    meal_type_enum.create(op.get_bind(), checkfirst=True)

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── user_profiles ─────────────────────────────────────────────────────────
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("sex", sa.Enum("male", "female", "other", name="sex"), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=False),
        sa.Column(
            "activity_level",
            sa.Enum(
                "sedentary", "lightly_active", "moderately_active", "very_active", "extra_active",
                name="activitylevel",
            ),
            nullable=False,
        ),
        sa.Column("goal", sa.Enum("maintain", "cut", "bulk", name="goal"), nullable=False),
        sa.Column("daily_targets_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("body_composition_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )

    # ── products ──────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("serving_size_g", sa.Float(), nullable=False),
        # serving_quantity / serving_unit — added in ensure_dev_schema (now in initial migration)
        sa.Column("serving_quantity", sa.Float(), nullable=True),
        sa.Column("serving_unit", sa.String(), nullable=True),
        # is_favorite — added in ensure_dev_schema
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("protein_g", sa.Float(), nullable=False, server_default="0"),
        sa.Column("carbs_g", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fat_g", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sugar_g", sa.Float(), nullable=True),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("sodium_mg", sa.Float(), nullable=True),
        sa.Column("other_nutrients_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("source_pdf_path", sa.String(), nullable=True),
        # chroma_indexed — Issue 14: track embedding state
        sa.Column("chroma_indexed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_index("ix_products_user_id", "products", ["user_id"])

    # ── meal_entries ──────────────────────────────────────────────────────────
    op.create_table(
        "meal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "meal_type",
            sa.Enum("breakfast", "lunch", "dinner", "snack", name="mealtype"),
            nullable=False,
        ),
        sa.Column(
            "logged_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("raw_text", sa.String(), nullable=False),
        sa.Column("parsed_items_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_meal_entries_user_id", "meal_entries", ["user_id"])
    op.create_index("ix_meal_entries_logged_at", "meal_entries", ["logged_at"])

    # ── meal_items ────────────────────────────────────────────────────────────
    op.create_table(
        "meal_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "meal_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("meal_entries.id"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id"),
            nullable=True,
        ),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("resolved_nutrients_json", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
    )

    # ── refresh_tokens — Issue 6/8 ────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("meal_items")
    op.drop_table("meal_entries")
    op.drop_table("products")
    op.drop_table("user_profiles")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS mealtype")
    op.execute("DROP TYPE IF EXISTS goal")
    op.execute("DROP TYPE IF EXISTS activitylevel")
    op.execute("DROP TYPE IF EXISTS sex")
