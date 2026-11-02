"""Reported winery sales

Revision ID: 0005_winery_sales
Revises: 0004_deal_financials
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_winery_sales"
down_revision = "0004_deal_financials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "winery_sale",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("location", sa.String(256)),
        sa.Column("sold_year", sa.Integer(), nullable=False),
        sa.Column("sale_price", sa.Float(), nullable=False),
        sa.Column("last_asking_price", sa.Float()),
        sa.Column("total_acres", sa.Float()),
        sa.Column("planted_acres", sa.Float()),
        sa.Column("sale_type", sa.String(32), nullable=False),
        sa.Column("evidence", sa.String(32), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("source_url", sa.String(1024)),
        sa.UniqueConstraint("name", "sold_year", name="uq_winery_sale"),
    )


def downgrade() -> None:
    op.drop_table("winery_sale")
