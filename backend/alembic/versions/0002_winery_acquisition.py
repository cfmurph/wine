"""Winery acquisition tables

Revision ID: 0002_winery_acquisition
Revises: 0001_initial
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002_winery_acquisition"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "winery",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("licence_number", sa.String(32), nullable=False),
        sa.Column("licensee", sa.String(256)),
        sa.Column("street", sa.String(256)),
        sa.Column("city", sa.String(128)),
        sa.Column("local_government", sa.String(128)),
        sa.Column("postal_code", sa.String(16)),
        sa.Column("region", sa.String(64)),
        sa.Column("province", sa.String(64)),
        sa.Column("licence_expiry", sa.Date()),
        sa.Column("endorsements", JSONB),
        sa.Column("service_capacity", sa.Integer()),
        sa.Column("case_production", sa.Integer()),
        sa.Column("vineyard_acres", sa.Float()),
        sa.Column("source", sa.String(64)),
        sa.Column("source_date", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_winery_name", "winery", ["name"])
    op.create_index("ix_winery_licence_number", "winery", ["licence_number"], unique=True)
    op.create_index("ix_winery_region", "winery", ["region"])

    op.add_column("wine", sa.Column("bc_sku", sa.String(32)))
    op.add_column("wine", sa.Column("winery_id", sa.String(), sa.ForeignKey("winery.id", ondelete="SET NULL")))
    op.add_column("wine", sa.Column("winery_match_status", sa.String(16)))
    op.create_index("ix_wine_bc_sku", "wine", ["bc_sku"], unique=True)
    op.create_index("ix_wine_winery_id", "wine", ["winery_id"])

    op.create_table(
        "price_snapshot",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("wine_id", sa.String(), sa.ForeignKey("wine.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False),
        sa.Column("litres", sa.Float()),
        sa.UniqueConstraint("wine_id", "source", "observed_on", name="uq_price_snapshot"),
    )
    op.create_index("ix_price_snapshot_wine_id", "price_snapshot", ["wine_id"])

    op.create_table(
        "winery_listing",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("winery_id", sa.String(), sa.ForeignKey("winery.id", ondelete="SET NULL")),
        sa.Column("advertised_name", sa.String(256), nullable=False),
        sa.Column("location", sa.String(256)),
        sa.Column("asking_price", sa.Float()),
        sa.Column("previous_asking_price", sa.Float()),
        sa.Column("currency", sa.String(8)),
        sa.Column("total_acres", sa.Float()),
        sa.Column("planted_acres", sa.Float()),
        sa.Column("capacity_cases", sa.Integer()),
        sa.Column("includes_licence", sa.Boolean()),
        sa.Column("includes_brand", sa.Boolean()),
        sa.Column("includes_inventory", sa.Boolean()),
        sa.Column("includes_equipment", sa.Boolean()),
        sa.Column("status", sa.String(64)),
        sa.Column("notes", sa.Text()),
        sa.Column("source_url", sa.String(1024)),
        sa.Column("as_of", sa.Date()),
        sa.UniqueConstraint("advertised_name", "as_of", name="uq_winery_listing"),
    )
    op.create_index("ix_winery_listing_winery_id", "winery_listing", ["winery_id"])

    op.create_table(
        "market_stat",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("period", sa.String(16), nullable=False),
        sa.Column("geography", sa.String(64), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("metric", sa.String(32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(16), nullable=False),
        sa.UniqueConstraint("source", "period", "geography", "category", "metric", name="uq_market_stat"),
    )


def downgrade() -> None:
    op.drop_table("market_stat")
    op.drop_table("winery_listing")
    op.drop_table("price_snapshot")
    op.drop_index("ix_wine_winery_id", table_name="wine")
    op.drop_index("ix_wine_bc_sku", table_name="wine")
    op.drop_column("wine", "winery_match_status")
    op.drop_column("wine", "winery_id")
    op.drop_column("wine", "bc_sku")
    op.drop_table("winery")
