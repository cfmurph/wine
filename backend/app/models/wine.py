import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey,
    UniqueConstraint, Enum as SAEnum, Boolean,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


def _uuid():
    return str(uuid.uuid4())


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    scores = relationship("WineScore", back_populates="wine", cascade="all, delete-orphan")
    prices = relationship("WinePrice", back_populates="wine", cascade="all, delete-orphan")
    pairings = relationship("Pairing", back_populates="wine", cascade="all, delete-orphan")
    user_wines = relationship("UserWine", back_populates="wine", cascade="all, delete-orphan")


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


class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String(256), unique=True, index=True, nullable=False)
    username = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_wines = relationship("UserWine", back_populates="user", cascade="all, delete-orphan")


class UserWine(Base):
    __tablename__ = "user_wine"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    wine_id = Column(String, ForeignKey("wine.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(
        SAEnum("favorite", "tried", "want_to_try", "cellar", name="user_wine_status"),
        nullable=False,
    )
    user_rating = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "wine_id", name="uq_user_wine"),)

    user = relationship("User", back_populates="user_wines")
    wine = relationship("Wine", back_populates="user_wines")
