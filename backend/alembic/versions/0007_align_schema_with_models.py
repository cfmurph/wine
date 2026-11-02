"""Align the original schema with the models

Adds indexes the models declare, and replaces unique constraints with the unique indexes they expect.

Revision ID: 0007_align_schema_with_models
Revises: 0006_winery_land_check
Create Date: 2026-11-02
"""
from alembic import op

revision = "0007_align_schema_with_models"
down_revision = "0006_winery_land_check"
branch_labels = None
depends_on = None

_ADDED_INDEXES = (
    ("ix_pairing_wine_id", "pairing", "wine_id"),
    ("ix_user_wine_user_id", "user_wine", "user_id"),
    ("ix_user_wine_wine_id", "user_wine", "wine_id"),
    ("ix_wine_global_wine_score_id", "wine", "global_wine_score_id"),
    ("ix_wine_price_wine_id", "wine_price", "wine_id"),
    ("ix_wine_score_wine_id", "wine_score", "wine_id"),
)


def upgrade() -> None:
    for name, table, column in _ADDED_INDEXES:
        op.create_index(name, table, [column])
    op.create_index("ix_user_email", "user", ["email"], unique=True)
    op.drop_constraint("user_email_key", "user", type_="unique")
    op.create_index("ix_user_username", "user", ["username"], unique=True)
    op.drop_constraint("user_username_key", "user", type_="unique")
    op.drop_index("ix_wine_wine_searcher_id", table_name="wine")
    op.create_index("ix_wine_wine_searcher_id", "wine", ["wine_searcher_id"], unique=True)
    op.drop_constraint("wine_wine_searcher_id_key", "wine", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("wine_wine_searcher_id_key", "wine", ["wine_searcher_id"])
    op.drop_index("ix_wine_wine_searcher_id", table_name="wine")
    op.create_index("ix_wine_wine_searcher_id", "wine", ["wine_searcher_id"])
    op.create_unique_constraint("user_username_key", "user", ["username"])
    op.drop_index("ix_user_username", table_name="user")
    op.create_unique_constraint("user_email_key", "user", ["email"])
    op.drop_index("ix_user_email", table_name="user")
    for name, _, _ in _ADDED_INDEXES:
        op.drop_index(name)
