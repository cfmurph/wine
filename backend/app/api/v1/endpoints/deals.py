from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import User
from app.schemas.deal import (
    DealAssumptions, DealComparisonOut, DealCreate, DealFinancialsOut, DealItemCreate, DealItemOut, DealItemUpdate,
    DealOut, DealUpdate,
    FinancialYearIn, FinancingIn, FinancingOut,
)
from app.services import deal_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/users/me/deals", tags=["deals"])


@router.get("", response_model=list[DealOut])
async def list_deals(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await deal_service.list_deals(db, user.id)


@router.get("/compare", response_model=list[DealComparisonOut])
async def compare_deals(
    worst_revenue: float = Query(-15, ge=-100, le=100, description="Percent change in revenue"),
    worst_costs: float = Query(10, ge=-100, le=100, description="Percent change in costs"),
    best_revenue: float = Query(10, ge=-100, le=100),
    best_costs: float = Query(-5, ge=-100, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await deal_service.compare_deals(
        db, user.id, (worst_revenue / 100, worst_costs / 100), (best_revenue / 100, best_costs / 100)
    )


@router.post("", response_model=DealOut)
async def create_deal(payload: DealCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await deal_service.create_deal(db, user.id, payload)


@router.patch("/{deal_id}", response_model=DealOut)
async def update_deal(
    deal_id: str, payload: DealUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await deal_service.update_deal(db, user.id, deal_id, payload)


@router.delete("/{deal_id}", status_code=204)
async def delete_deal(deal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await deal_service.delete_deal(db, user.id, deal_id)


@router.post("/{deal_id}/items", response_model=DealItemOut)
async def add_item(
    deal_id: str, payload: DealItemCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await deal_service.add_item(db, user.id, deal_id, payload)


@router.patch("/{deal_id}/items/{item_id}", response_model=DealItemOut)
async def update_item(
    deal_id: str,
    item_id: str,
    payload: DealItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await deal_service.update_item(db, user.id, deal_id, item_id, payload)


@router.delete("/{deal_id}/items/{item_id}", status_code=204)
async def delete_item(
    deal_id: str, item_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await deal_service.delete_item(db, user.id, deal_id, item_id)


@router.get("/{deal_id}/financials", response_model=DealFinancialsOut)
async def get_financials(deal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await deal_service.get_financials(db, user.id, deal_id)


@router.put("/{deal_id}/financials/assumptions", response_model=DealFinancialsOut)
async def set_assumptions(
    deal_id: str, payload: DealAssumptions, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await deal_service.set_assumptions(db, user.id, deal_id, payload)


@router.put("/{deal_id}/financials/years/{fiscal_year}", response_model=DealFinancialsOut)
async def set_financial_year(
    deal_id: str,
    payload: FinancialYearIn,
    fiscal_year: int = Path(ge=1980, le=2100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await deal_service.set_financial_year(db, user.id, deal_id, fiscal_year, payload)


@router.delete("/{deal_id}/financials/years/{fiscal_year}", response_model=DealFinancialsOut)
async def delete_financial_year(
    deal_id: str, fiscal_year: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await deal_service.delete_financial_year(db, user.id, deal_id, fiscal_year)


@router.post("/{deal_id}/financing", response_model=FinancingOut)
async def model_financing(
    deal_id: str, payload: FinancingIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await deal_service.get_financing(db, user.id, deal_id, payload)
