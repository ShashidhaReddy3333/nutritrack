"""Security and reliability hardening.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-21 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("privacy_consent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("products", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"))
    op.create_index("ix_products_is_deleted", "products", ["is_deleted"])
    op.add_column("meal_items", sa.Column("product_name_snapshot", sa.String(), nullable=True))
    op.add_column("meal_items", sa.Column("product_brand_snapshot", sa.String(), nullable=True))
    op.execute(
        """
        UPDATE meal_items
        SET product_name_snapshot = products.name,
            product_brand_snapshot = products.brand
        FROM products
        WHERE meal_items.product_id = products.id
        """
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_token_hash", table_name="password_reset_tokens")
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_column("meal_items", "product_brand_snapshot")
    op.drop_column("meal_items", "product_name_snapshot")
    op.drop_index("ix_products_is_deleted", table_name="products")
    op.drop_column("products", "is_deleted")
    op.drop_column("users", "privacy_consent_at")
