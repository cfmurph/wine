from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

DealStage = Literal["researching", "contacted", "nda", "financials", "offer", "closed", "passed"]
DealItemKind = Literal["document", "advisor"]


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
