from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class WineScoreOut(BaseModel):
    provider: str
    score: Optional[float] = None
    score_scale: int = 100
    review_count: Optional[int] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WinePriceOut(BaseModel):
    provider: str
    currency: str = "USD"
    min_price: Optional[float] = None
    avg_price: Optional[float] = None
    max_price: Optional[float] = None
    purchase_url: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PairingOut(BaseModel):
    food_name: str
    confidence: Optional[float] = None
    provider: Optional[str] = None

    model_config = {"from_attributes": True}


class WineSearchResult(BaseModel):
    id: str
    canonical_name: str
    producer: Optional[str] = None
    vintage: Optional[int] = None
    country: Optional[str] = None
    region: Optional[str] = None
    style: Optional[str] = None
    avg_score: Optional[float] = None
    avg_price: Optional[float] = None
    currency: str = "USD"
    image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class WineSearchResponse(BaseModel):
    results: List[WineSearchResult]
    total: int
    page: int = 1
    per_page: int = 20


class WineDetail(BaseModel):
    id: str
    canonical_name: str
    producer: Optional[str] = None
    vintage: Optional[int] = None
    country: Optional[str] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    appellation: Optional[str] = None
    grape_varieties: List[str] = []
    style: Optional[str] = None
    abv: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    scores: List[WineScoreOut] = []
    prices: List[WinePriceOut] = []
    pairings: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WineCompareRequest(BaseModel):
    wine_ids: List[str] = Field(..., min_length=2, max_length=4)


class WineCompareItem(BaseModel):
    id: str
    canonical_name: str
    producer: Optional[str] = None
    vintage: Optional[int] = None
    country: Optional[str] = None
    region: Optional[str] = None
    grape_varieties: List[str] = []
    style: Optional[str] = None
    avg_score: Optional[float] = None
    avg_price: Optional[float] = None
    currency: str = "USD"
    value_score: Optional[float] = None


class WineCompareResponse(BaseModel):
    wines: List[WineCompareItem]


class PairingSearchResponse(BaseModel):
    food: str
    wine_types: List[str]
    wines: List[WineSearchResult]
    provider: str = "spoonacular"
