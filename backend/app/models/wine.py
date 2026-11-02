import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey,
    UniqueConstraint, Enum as SAEnum, Boolean, Date,
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


class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String(256), unique=True, index=True, nullable=False)
    username = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_wines = relationship("UserWine", back_populates="user", cascade="all, delete-orphan")
    deals = relationship("Deal", back_populates="user", cascade="all, delete-orphan")


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


class Winery(Base):
    __tablename__ = "winery"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(256), nullable=False, index=True)
    licence_number = Column(String(32), unique=True, index=True, nullable=False)
    licensee = Column(String(256))
    street = Column(String(256))
    city = Column(String(128))
    local_government = Column(String(128))
    postal_code = Column(String(16))
    region = Column(String(64), index=True)
    province = Column(String(64), default="British Columbia")
    licence_expiry = Column(Date)
    endorsements = Column(JSONB, default=list)
    service_capacity = Column(Integer)
    case_production = Column(Integer)
    vineyard_acres = Column(Float)
    source = Column(String(64))
    source_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    wines = relationship("Wine", back_populates="winery")
    listings = relationship("WineryListing", back_populates="winery")


class PriceSnapshot(Base):
    __tablename__ = "price_snapshot"

    id = Column(String, primary_key=True, default=_uuid)
    wine_id = Column(String, ForeignKey("wine.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(64), nullable=False)
    observed_on = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="CAD")
    litres = Column(Float)

    __table_args__ = (UniqueConstraint("wine_id", "source", "observed_on", name="uq_price_snapshot"),)

    wine = relationship("Wine", back_populates="price_snapshots")


class WineryListing(Base):
    __tablename__ = "winery_listing"

    id = Column(String, primary_key=True, default=_uuid)
    winery_id = Column(String, ForeignKey("winery.id", ondelete="SET NULL"), index=True)
    advertised_name = Column(String(256), nullable=False)
    location = Column(String(256))
    asking_price = Column(Float)
    previous_asking_price = Column(Float)
    currency = Column(String(8), default="CAD")
    total_acres = Column(Float)
    planted_acres = Column(Float)
    capacity_cases = Column(Integer)
    # None means the listing doesn't say, which is different from False.
    includes_licence = Column(Boolean)
    includes_brand = Column(Boolean)
    includes_inventory = Column(Boolean)
    includes_equipment = Column(Boolean)
    status = Column(String(64))
    notes = Column(Text)
    source_url = Column(String(1024))
    as_of = Column(Date)

    __table_args__ = (UniqueConstraint("advertised_name", "as_of", name="uq_winery_listing"),)

    winery = relationship("Winery", back_populates="listings")


class MarketStat(Base):
    __tablename__ = "market_stat"

    id = Column(String, primary_key=True, default=_uuid)
    source = Column(String(64), nullable=False)
    period = Column(String(16), nullable=False)
    geography = Column(String(64), nullable=False)
    category = Column(String(64), nullable=False)
    metric = Column(String(32), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(16), nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "period", "geography", "category", "metric", name="uq_market_stat"),
    )


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_deal_user_name"),)

    user = relationship("User", back_populates="deals")
    winery = relationship("Winery")
    items = relationship(
        "DealItem", back_populates="deal", cascade="all, delete-orphan", order_by="DealItem.position"
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
