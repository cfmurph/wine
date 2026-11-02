"""Licensed wineries, sale listings, reported sales and market data."""

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey, UniqueConstraint, Boolean, Date,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.base import _uuid


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
    land_check = relationship("WineryLandCheck", back_populates="winery", uselist=False, cascade="all, delete-orphan")


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


class WineryLandCheck(Base):
    """Public map data around a winery's licensed address. None means not checked or unavailable."""

    __tablename__ = "winery_land_check"

    id = Column(String, primary_key=True, default=_uuid)
    winery_id = Column(String, ForeignKey("winery.id", ondelete="CASCADE"), nullable=False, unique=True)
    matched_address = Column(String(256))
    geocode_score = Column(Integer)
    address_reliable = Column(Boolean, nullable=False)
    in_alr = Column(Boolean)
    wells_nearby = Column(Integer)
    irrigation_wells_nearby = Column(Integer)
    fires_since_2000 = Column(Integer)
    latest_fire_year = Column(Integer)
    largest_fire_hectares = Column(Float)
    checked_on = Column(Date, nullable=False)

    winery = relationship("Winery", back_populates="land_check")


class WinerySale(Base):
    """A reported completed or court-approved sale, entered by hand from public sources."""

    __tablename__ = "winery_sale"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(256), nullable=False)
    location = Column(String(256))
    sold_year = Column(Integer, nullable=False)
    sale_price = Column(Float, nullable=False)
    last_asking_price = Column(Float)
    total_acres = Column(Float)
    planted_acres = Column(Float)
    sale_type = Column(String(32), nullable=False)
    evidence = Column(String(32), nullable=False)
    notes = Column(Text)
    source_url = Column(String(1024))

    __table_args__ = (UniqueConstraint("name", "sold_year", name="uq_winery_sale"),)


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
