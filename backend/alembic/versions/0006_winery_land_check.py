"""Winery land and risk checks

Revision ID: 0006_winery_land_check
Revises: 0005_winery_sales
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_winery_land_check"
down_revision = "0005_winery_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "winery_land_check",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("winery_id", sa.String(), sa.ForeignKey("winery.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("matched_address", sa.String(256)),
        sa.Column("geocode_score", sa.Integer()),
        sa.Column("address_reliable", sa.Boolean(), nullable=False),
        sa.Column("in_alr", sa.Boolean()),
        sa.Column("wells_nearby", sa.Integer()),
        sa.Column("irrigation_wells_nearby", sa.Integer()),
        sa.Column("fires_since_2000", sa.Integer()),
        sa.Column("latest_fire_year", sa.Integer()),
        sa.Column("largest_fire_hectares", sa.Float()),
        sa.Column("checked_on", sa.Date(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("winery_land_check")
