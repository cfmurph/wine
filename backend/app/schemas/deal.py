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
