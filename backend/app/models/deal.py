"""A user's private purchase pipeline. Deal data must never be committed to this repo."""

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey, UniqueConstraint, Boolean, Date,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.base import _uuid


class Deal(Base):
    __tablename__ = "deal"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    winery_id = Column(String, ForeignKey("winery.id", ondelete="SET NULL"), index=True)
    name = Column(String(256), nullable=False)
    stage = Column(String(32), nullable=False, default="researching")
    next_step = Column(String(512))
    next_step_due = Column(Date)
    notes = Column(Text)
    asking_price = Column(Float)
    property_value = Column(Float)
    owner_salary = Column(Float)
    working_capital = Column(Float)
    replanting_cost = Column(Float)
    equipment_cost = Column(Float)
    repair_cost = Column(Float)
    inventory_funding = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_deal_user_name"),)

    user = relationship("User", back_populates="deals")
    winery = relationship("Winery")
    items = relationship(
        "DealItem", back_populates="deal", cascade="all, delete-orphan", order_by="DealItem.position"
    )
    financials = relationship(
        "DealFinancial", back_populates="deal", cascade="all, delete-orphan", order_by="DealFinancial.fiscal_year"
    )


class DealItem(Base):
    __tablename__ = "deal_item"

    id = Column(String, primary_key=True, default=_uuid)
    deal_id = Column(String, ForeignKey("deal.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(16), nullable=False)
    title = Column(String(256), nullable=False)
    assignee = Column(String(256))
    done = Column(Boolean, nullable=False, default=False)
    position = Column(Integer, nullable=False, default=0)

    deal = relationship("Deal", back_populates="items")


class DealFinancial(Base):
    """One fiscal year of a seller's figures. Private to the deal's owner; blank means not provided."""

    __tablename__ = "deal_financial"

    id = Column(String, primary_key=True, default=_uuid)
    deal_id = Column(String, ForeignKey("deal.id", ondelete="CASCADE"), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False)
    revenue = Column(Float)
    tax_return_revenue = Column(Float)
    cost_of_goods = Column(Float)
    operating_expenses = Column(Float)
    owner_addbacks = Column(Float)
    cases_opening = Column(Float)
    cases_produced = Column(Float)
    cases_sold = Column(Float)
    cases_closing = Column(Float)
    grape_tonnes = Column(Float)
    channels = Column(JSONB, nullable=False, default=list)

    __table_args__ = (UniqueConstraint("deal_id", "fiscal_year", name="uq_deal_financial_year"),)

    deal = relationship("Deal", back_populates="financials")
