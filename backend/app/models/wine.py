"""Wines, critic scores, provider prices and food pairings."""

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.base import _uuid


class Wine(Base):
    __tablename__ = "wine"

    id = Column(String, primary_key=True, default=_uuid)
    canonical_name = Column(String(512), nullable=False, index=True)
    producer = Column(String(256))
    vintage = Column(Integer, index=True)
    country = Column(String(128), index=True)
    region = Column(String(256), index=True)
    subregion = Column(String(256))
    appellation = Column(String(256))
    grape_varieties = Column(JSONB, default=list)
    style = Column(String(64), index=True)
    abv = Column(Float)
    description = Column(Text)
    image_url = Column(String(1024))
    source_primary = Column(String(64))
    wine_searcher_id = Column(String(256), unique=True, index=True)
    global_wine_score_id = Column(String(256), index=True)
    bc_sku = Column(String(32), unique=True, index=True)
    winery_id = Column(String, ForeignKey("winery.id", ondelete="SET NULL"), index=True)
    winery_match_status = Column(String(16))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    scores = relationship("WineScore", back_populates="wine", cascade="all, delete-orphan")
    prices = relationship("WinePrice", back_populates="wine", cascade="all, delete-orphan")
    pairings = relationship("Pairing", back_populates="wine", cascade="all, delete-orphan")
    user_wines = relationship("UserWine", back_populates="wine", cascade="all, delete-orphan")
    price_snapshots = relationship("PriceSnapshot", back_populates="wine", cascade="all, delete-orphan")
    winery = relationship("Winery", back_populates="wines")


class WineScore(Base):
    __tablename__ = "wine_score"

    id = Column(String, primary_key=True, default=_uuid)
    wine_id = Column(String, ForeignKey("wine.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    score = Column(Float)
    score_scale = Column(Integer, default=100)
    review_count = Column(Integer)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("wine_id", "provider", name="uq_wine_score_provider"),)

    wine = relationship("Wine", back_populates="scores")


class WinePrice(Base):
    __tablename__ = "wine_price"

    id = Column(String, primary_key=True, default=_uuid)
    wine_id = Column(String, ForeignKey("wine.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    currency = Column(String(8), default="USD")
    min_price = Column(Float)
    avg_price = Column(Float)
    max_price = Column(Float)
    purchase_url = Column(String(1024))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("wine_id", "provider", name="uq_wine_price_provider"),)

    wine = relationship("Wine", back_populates="prices")


class Pairing(Base):
    __tablename__ = "pairing"

    id = Column(String, primary_key=True, default=_uuid)
    wine_id = Column(String, ForeignKey("wine.id", ondelete="CASCADE"), nullable=False, index=True)
    food_name = Column(String(256), nullable=False)
    confidence = Column(Float)
    provider = Column(String(64))

    __table_args__ = (UniqueConstraint("wine_id", "food_name", name="uq_pairing_wine_food"),)

    wine = relationship("Wine", back_populates="pairings")
