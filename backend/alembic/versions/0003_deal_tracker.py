"""Deal tracker tables

Revision ID: 0003_deal_tracker
Revises: 0002_winery_acquisition
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_deal_tracker"
down_revision = "0002_winery_acquisition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deal",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("winery_id", sa.String(), sa.ForeignKey("winery.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("next_step", sa.String(512)),
        sa.Column("next_step_due", sa.Date()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "name", name="uq_deal_user_name"),
    )
    op.create_index("ix_deal_user_id", "deal", ["user_id"])
    op.create_index("ix_deal_winery_id", "deal", ["winery_id"])
    op.create_table(
        "deal_item",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("deal_id", sa.String(), sa.ForeignKey("deal.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("assignee", sa.String(256)),
        sa.Column("done", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
    )
    op.create_index("ix_deal_item_deal_id", "deal_item", ["deal_id"])


def downgrade() -> None:
    op.drop_table("deal_item")
    op.drop_table("deal")
