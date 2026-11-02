"""Import every model here, so relationships resolve and migrations see all tables."""

from app.models.wine import Wine, WineScore, WinePrice, Pairing
from app.models.user import User, UserWine
from app.models.winery import Winery, PriceSnapshot, WineryListing, WineryLandCheck, WinerySale, MarketStat
from app.models.deal import Deal, DealItem, DealFinancial

__all__ = [
    "Wine",
    "WineScore",
    "WinePrice",
    "Pairing",
    "User",
    "UserWine",
    "Winery",
    "PriceSnapshot",
    "WineryListing",
    "WineryLandCheck",
    "WinerySale",
    "MarketStat",
    "Deal",
    "DealItem",
    "DealFinancial",
]
