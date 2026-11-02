"""Private deal financials

Revision ID: 0004_deal_financials
Revises: 0003_deal_tracker
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_deal_financials"
down_revision = "0003_deal_tracker"
branch_labels = None
depends_on = None

_ASSUMPTIONS = (
    "asking_price", "property_value", "owner_salary", "working_capital",
    "replanting_cost", "equipment_cost", "repair_cost", "inventory_funding",
)


def upgrade() -> None:
    for name in _ASSUMPTIONS:
        op.add_column("deal", sa.Column(name, sa.Float()))
    op.create_table(
        "deal_financial",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("deal_id", sa.String(), sa.ForeignKey("deal.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("revenue", sa.Float()),
        sa.Column("tax_return_revenue", sa.Float()),
        sa.Column("cost_of_goods", sa.Float()),
        sa.Column("operating_expenses", sa.Float()),
        sa.Column("owner_addbacks", sa.Float()),
        sa.Column("cases_opening", sa.Float()),
        sa.Column("cases_produced", sa.Float()),
        sa.Column("cases_sold", sa.Float()),
        sa.Column("cases_closing", sa.Float()),
        sa.Column("grape_tonnes", sa.Float()),
        sa.Column("channels", JSONB(), nullable=False),
        sa.UniqueConstraint("deal_id", "fiscal_year", name="uq_deal_financial_year"),
    )
    op.create_index("ix_deal_financial_deal_id", "deal_financial", ["deal_id"])


def downgrade() -> None:
    op.drop_table("deal_financial")
    for name in _ASSUMPTIONS:
        op.drop_column("deal", name)
