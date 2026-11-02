from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

DealStage = Literal["researching", "contacted", "nda", "financials", "offer", "closed", "passed"]
DealItemKind = Literal["document", "advisor"]
SalesChannel = Literal["tasting_room", "wine_club", "online", "restaurants", "liquor_stores", "private_retail"]
Money = Optional[float]


class DealCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    winery_id: Optional[str] = None


class DealUpdate(BaseModel):
    stage: Optional[DealStage] = None
    next_step: Optional[str] = Field(None, max_length=512)
    next_step_due: Optional[date] = None
    notes: Optional[str] = None


class DealItemCreate(BaseModel):
    kind: DealItemKind
    title: str = Field(min_length=1, max_length=256)


class DealItemUpdate(BaseModel):
    done: Optional[bool] = None
    assignee: Optional[str] = Field(None, max_length=256)


class DealItemOut(BaseModel):
    id: str
    kind: str
    title: str
    assignee: Optional[str] = None
    done: bool

    model_config = {"from_attributes": True}


class DealOut(BaseModel):
    id: str
    winery_id: Optional[str] = None
    name: str
    stage: str
    next_step: Optional[str] = None
    next_step_due: Optional[date] = None
    notes: Optional[str] = None
    items: list[DealItemOut] = []

    model_config = {"from_attributes": True}


class DealAssumptions(BaseModel):
    asking_price: Money = Field(None, ge=0)
    property_value: Money = Field(None, ge=0)
    owner_salary: Money = Field(None, ge=0)
    working_capital: Money = Field(None, ge=0)
    replanting_cost: Money = Field(None, ge=0)
    equipment_cost: Money = Field(None, ge=0)
    repair_cost: Money = Field(None, ge=0)
    inventory_funding: Money = Field(None, ge=0)

    model_config = {"from_attributes": True}


class ChannelFigures(BaseModel):
    channel: SalesChannel
    cases: Money = Field(None, ge=0)
    revenue: Money = Field(None, ge=0)
    direct_cost: Money = Field(None, ge=0)


class FinancialYearIn(BaseModel):
    revenue: Money = Field(None, ge=0)
    tax_return_revenue: Money = Field(None, ge=0)
    cost_of_goods: Money = Field(None, ge=0)
    operating_expenses: Money = Field(None, ge=0)
    owner_addbacks: Money = Field(None, ge=0)
    cases_opening: Money = Field(None, ge=0)
    cases_produced: Money = Field(None, ge=0)
    cases_sold: Money = Field(None, ge=0)
    cases_closing: Money = Field(None, ge=0)
    grape_tonnes: Money = Field(None, ge=0)
    channels: list[ChannelFigures] = []


class FinancialYearOut(FinancialYearIn):
    fiscal_year: int

    model_config = {"from_attributes": True}


class CheckLine(BaseModel):
    label: str
    value: Optional[float] = None
    unit: Literal["currency", "multiple", "percent", "number"]


class AnalysisCheck(BaseModel):
    title: str
    status: Literal["computed", "review", "unknown"]
    note: str
    lines: list[CheckLine]


class DealFinancialsOut(BaseModel):
    deal_id: str
    name: str
    assumptions: DealAssumptions
    years: list[FinancialYearOut]
    analysis_year: Optional[int] = None
    checks: list[AnalysisCheck]


class ScenarioOut(BaseModel):
    name: Literal["Worst", "Expected", "Best"]
    revenue_change: float
    cost_change: float
    earnings: Optional[float] = None
    price_to_earnings: Optional[float] = None


class DealComparisonOut(BaseModel):
    deal_id: str
    name: str
    stage: str
    analysis_year: Optional[int] = None
    asking_price: Optional[float] = None
    revenue: Optional[float] = None
    cases_sold: Optional[float] = None
    property_share: Optional[float] = None
    total_cash_needed: Optional[float] = None
    review_count: int
    unknown_count: int
    scenarios: list[ScenarioOut]


class FinancingIn(BaseModel):
    purchase_price: Money = Field(None, ge=0)
    down_payment_percent: float = Field(ge=0, le=100)
    annual_rate_percent: float = Field(ge=0, le=40)
    amortization_years: int = Field(ge=1, le=40)
    available_cash: Money = Field(None, ge=0)
    min_coverage: float = Field(1.25, ge=1, le=3)
    rate_stress_points: float = Field(2.0, ge=0, le=20)


class FinancingOut(BaseModel):
    purchase_price: Optional[float] = None
    down_payment: Optional[float] = None
    loan: Optional[float] = None
    monthly_payment: Optional[float] = None
    annual_debt_service: Optional[float] = None
    adjusted_earnings: Optional[float] = None
    analysis_year: Optional[int] = None
    coverage: Optional[float] = None
    stressed_coverage: Optional[float] = None
    max_loan_from_earnings: Optional[float] = None
    other_cash_costs: float
    missing_cash_costs: list[str]
    cash_needed: Optional[float] = None
    cash_shortfall: Optional[float] = None
    max_price_for_cash: Optional[float] = None
