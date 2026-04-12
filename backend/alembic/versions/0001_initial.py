"""Initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wine",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("canonical_name", sa.String(512), nullable=False),
        sa.Column("producer", sa.String(256)),
        sa.Column("vintage", sa.Integer()),
        sa.Column("country", sa.String(128)),
        sa.Column("region", sa.String(256)),
        sa.Column("subregion", sa.String(256)),
        sa.Column("appellation", sa.String(256)),
        sa.Column("grape_varieties", JSONB),
        sa.Column("style", sa.String(64)),
        sa.Column("abv", sa.Float()),
        sa.Column("description", sa.Text()),
        sa.Column("image_url", sa.String(1024)),
        sa.Column("source_primary", sa.String(64)),
        sa.Column("wine_searcher_id", sa.String(256), unique=True),
        sa.Column("global_wine_score_id", sa.String(256)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_wine_canonical_name", "wine", ["canonical_name"])
    op.create_index("ix_wine_vintage", "wine", ["vintage"])
    op.create_index("ix_wine_country", "wine", ["country"])
    op.create_index("ix_wine_region", "wine", ["region"])
    op.create_index("ix_wine_style", "wine", ["style"])
    op.create_index("ix_wine_wine_searcher_id", "wine", ["wine_searcher_id"])

    op.create_table(
        "wine_score",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("wine_id", sa.String(), sa.ForeignKey("wine.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("score", sa.Float()),
        sa.Column("score_scale", sa.Integer(), default=100),
        sa.Column("review_count", sa.Integer()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("wine_id", "provider", name="uq_wine_score_provider"),
    )

    op.create_table(
        "wine_price",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("wine_id", sa.String(), sa.ForeignKey("wine.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("currency", sa.String(8), default="USD"),
        sa.Column("min_price", sa.Float()),
        sa.Column("avg_price", sa.Float()),
        sa.Column("max_price", sa.Float()),
        sa.Column("purchase_url", sa.String(1024)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("wine_id", "provider", name="uq_wine_price_provider"),
    )

    op.create_table(
        "pairing",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("wine_id", sa.String(), sa.ForeignKey("wine.id", ondelete="CASCADE"), nullable=False),
        sa.Column("food_name", sa.String(256), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("provider", sa.String(64)),
        sa.UniqueConstraint("wine_id", "food_name", name="uq_pairing_wine_food"),
    )

    op.create_table(
        "user",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(256), unique=True, nullable=False),
        sa.Column("username", sa.String(128), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "user_wine",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wine_id", sa.String(), sa.ForeignKey("wine.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("favorite", "tried", "want_to_try", "cellar", name="user_wine_status"), nullable=False),
        sa.Column("user_rating", sa.Float()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "wine_id", name="uq_user_wine"),
    )


def downgrade() -> None:
    op.drop_table("user_wine")
    op.drop_table("user")
    op.drop_table("pairing")
    op.drop_table("wine_price")
    op.drop_table("wine_score")
    op.drop_table("wine")
    op.execute("DROP TYPE IF EXISTS user_wine_status")
