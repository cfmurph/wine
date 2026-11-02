from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field


class ScoreComponentOut(BaseModel):
    label: str
    score: Optional[float] = None
    detail: str

    model_config = {"from_attributes": True}


class SubScoreOut(BaseModel):
    score: Optional[float] = None
    available: int
    total: int
    components: List[ScoreComponentOut]

    model_config = {"from_attributes": True}


class WineryListingOut(BaseModel):
    id: str
    winery_id: Optional[str] = None
    advertised_name: str
    location: Optional[str] = None
    asking_price: Optional[float] = None
    previous_asking_price: Optional[float] = None
    currency: str = "CAD"
    total_acres: Optional[float] = None
    planted_acres: Optional[float] = None
    capacity_cases: Optional[int] = None
    includes_licence: Optional[bool] = None
    includes_brand: Optional[bool] = None
    includes_inventory: Optional[bool] = None
    includes_equipment: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None
    as_of: Optional[date] = None

    model_config = {"from_attributes": True}


class WinerySummary(BaseModel):
    id: str
    name: str
    city: Optional[str] = None
    region: Optional[str] = None
    wine_count: int
    median_bottle_price: Optional[float] = None
    avg_critic_score: Optional[float] = None
    production_cases: Optional[int] = None
    asking_price: Optional[float] = None
    listing_status: Optional[str] = None
    overall_score: Optional[float] = None
    sub_scores: dict[str, SubScoreOut]


class WineryListResponse(BaseModel):
    results: List[WinerySummary]
    total: int
    regions: List[str]


class WineryWineOut(BaseModel):
    id: str
    name: str
    style: Optional[str] = None
    vintage: Optional[int] = None
    retail_price_cad: Optional[float] = None
    litres: Optional[float] = None
    price_date: Optional[date] = None
    critic_score: Optional[float] = None
    historical_price_usd: Optional[float] = None


class DataSourceOut(BaseModel):
    label: str
    as_of: Optional[str] = None
    url: Optional[str] = None


class WineryDetail(WinerySummary):
    licence_number: str
    licensee: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    licence_expiry: Optional[date] = None
    endorsements: List[str] = []
    service_capacity: Optional[int] = None
    wines: List[WineryWineOut]
    listings: List[WineryListingOut]
    sources: List[DataSourceOut]


class WineryCompareRequest(BaseModel):
    winery_ids: List[str] = Field(..., min_length=2, max_length=4)
    brand: float = Field(1.0, ge=0)
    land: float = Field(1.0, ge=0)
    tourism: float = Field(1.0, ge=0)
    operations: float = Field(1.0, ge=0)


class WineryCompareResponse(BaseModel):
    wineries: List[WineryDetail]


class MarketStatOut(BaseModel):
    period: str
    geography: str
    metric: str
    value: float
    unit: str

    model_config = {"from_attributes": True}


class PriceBucketOut(BaseModel):
    label: str
    count: int


class WinerySaleOut(BaseModel):
    id: str
    name: str
    location: Optional[str] = None
    sold_year: int
    sale_price: float
    last_asking_price: Optional[float] = None
    total_acres: Optional[float] = None
    planted_acres: Optional[float] = None
    sale_type: str
    evidence: str
    notes: Optional[str] = None
    source_url: Optional[str] = None

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def share_of_asking(self) -> Optional[float]:
        return self.sale_price / self.last_asking_price if self.last_asking_price else None


class MarketResponse(BaseModel):
    stats: List[MarketStatOut]
    stats_source: DataSourceOut
    price_buckets: List[PriceBucketOut]
    median_bottle_price: Optional[float] = None
    priced_bottles: int
    price_date: Optional[date] = None
    price_source: DataSourceOut
    listings: List[WineryListingOut]
    sales: List[WinerySaleOut]
    reports: List[DataSourceOut]
