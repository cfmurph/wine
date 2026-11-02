"""Deal tracker: each user's private purchase pipeline. Every query filters by user."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.wine import Deal, DealFinancial, DealItem, Winery
from app.schemas.deal import (
    DealAssumptions, DealComparisonOut, DealCreate, DealFinancialsOut, DealItemCreate, DealItemUpdate, DealUpdate,
    FinancialYearIn, FinancialYearOut,
)
from app.services.deal_analysis import analyze_deal, compare_deal

DEFAULT_ITEMS = [
    ("document", "Financial statements and tax returns, 3 to 5 years"),
    ("document", "Bottle sales by wine, vintage and channel"),
    ("document", "Costs per bottle or case"),
    ("document", "Inventory by vintage, with valuation"),
    ("document", "Vineyard blocks, yields and grape contracts"),
    ("document", "Licences, brand ownership, contracts, debts and liens"),
    ("document", "Title, ALR status, water licences, permits and zoning"),
    ("advisor", "Lawyer: NDA, purchase agreement and what transfers"),
    ("advisor", "Accountant: earnings, costs, inventory and excise"),
    ("advisor", "Appraiser: land, buildings, equipment and business"),
    ("advisor", "Vineyard inspection: vines, soil, yields and irrigation"),
    ("advisor", "Licensing: confirm the transfer path with the regulator"),
]


async def get_deal(db: AsyncSession, user_id: str, deal_id: str) -> Deal:
    deal = (await db.execute(
        select(Deal).options(selectinload(Deal.items)).where(Deal.id == deal_id, Deal.user_id == user_id)
    )).scalar_one_or_none()
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


async def list_deals(db: AsyncSession, user_id: str) -> list[Deal]:
    return list((await db.execute(
        select(Deal).options(selectinload(Deal.items)).where(Deal.user_id == user_id).order_by(Deal.created_at)
    )).scalars())


async def create_deal(db: AsyncSession, user_id: str, payload: DealCreate) -> Deal:
    existing = (await db.execute(
        select(Deal.id).where(Deal.user_id == user_id, Deal.name == payload.name)
    )).scalar_one_or_none()
    if existing:
        return await get_deal(db, user_id, existing)
    if payload.winery_id and await db.get(Winery, payload.winery_id) is None:
        raise HTTPException(status_code=404, detail="Winery not found")
    deal = Deal(user_id=user_id, name=payload.name, winery_id=payload.winery_id, stage="researching")
    deal.items = [DealItem(kind=kind, title=title, done=False, position=i) for i, (kind, title) in enumerate(DEFAULT_ITEMS)]
    db.add(deal)
    await db.flush()
    return await get_deal(db, user_id, deal.id)


async def update_deal(db: AsyncSession, user_id: str, deal_id: str, payload: DealUpdate) -> Deal:
    deal = await get_deal(db, user_id, deal_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "stage" and value is None:
            continue
        setattr(deal, field, value)
    await db.flush()
    return deal


async def delete_deal(db: AsyncSession, user_id: str, deal_id: str) -> None:
    await db.delete(await get_deal(db, user_id, deal_id))


async def add_item(db: AsyncSession, user_id: str, deal_id: str, payload: DealItemCreate) -> DealItem:
    deal = await get_deal(db, user_id, deal_id)
    item = DealItem(deal_id=deal.id, kind=payload.kind, title=payload.title, done=False, position=len(deal.items))
    db.add(item)
    await db.flush()
    return item


def _find_item(deal: Deal, item_id: str) -> DealItem:
    item = next((i for i in deal.items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


async def update_item(db: AsyncSession, user_id: str, deal_id: str, item_id: str, payload: DealItemUpdate) -> DealItem:
    item = _find_item(await get_deal(db, user_id, deal_id), item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "done" and value is None:
            continue
        setattr(item, field, value)
    await db.flush()
    return item


async def delete_item(db: AsyncSession, user_id: str, deal_id: str, item_id: str) -> None:
    await db.delete(_find_item(await get_deal(db, user_id, deal_id), item_id))


async def _deal_with_financials(db: AsyncSession, user_id: str, deal_id: str) -> Deal:
    deal = (await db.execute(
        select(Deal).options(selectinload(Deal.financials)).where(Deal.id == deal_id, Deal.user_id == user_id)
    )).scalar_one_or_none()
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


def _financials_out(deal: Deal) -> DealFinancialsOut:
    analysis_year, checks = analyze_deal(deal, deal.financials)
    return DealFinancialsOut(
        deal_id=deal.id,
        name=deal.name,
        assumptions=DealAssumptions.model_validate(deal),
        years=[FinancialYearOut.model_validate(y) for y in deal.financials],
        analysis_year=analysis_year,
        checks=checks,
    )


async def get_financials(db: AsyncSession, user_id: str, deal_id: str) -> DealFinancialsOut:
    return _financials_out(await _deal_with_financials(db, user_id, deal_id))


async def set_assumptions(db: AsyncSession, user_id: str, deal_id: str, payload: DealAssumptions) -> DealFinancialsOut:
    deal = await _deal_with_financials(db, user_id, deal_id)
    for field, value in payload.model_dump().items():
        setattr(deal, field, value)
    await db.flush()
    return _financials_out(deal)


async def set_financial_year(
    db: AsyncSession, user_id: str, deal_id: str, fiscal_year: int, payload: FinancialYearIn
) -> DealFinancialsOut:
    deal = await _deal_with_financials(db, user_id, deal_id)
    year = next((y for y in deal.financials if y.fiscal_year == fiscal_year), None)
    if year is None:
        year = DealFinancial(fiscal_year=fiscal_year)
        deal.financials.append(year)
    for field, value in payload.model_dump().items():
        setattr(year, field, value)
    deal.financials.sort(key=lambda y: y.fiscal_year)
    await db.flush()
    return _financials_out(deal)


async def delete_financial_year(db: AsyncSession, user_id: str, deal_id: str, fiscal_year: int) -> DealFinancialsOut:
    deal = await _deal_with_financials(db, user_id, deal_id)
    year = next((y for y in deal.financials if y.fiscal_year == fiscal_year), None)
    if year is None:
        raise HTTPException(status_code=404, detail="Year not found")
    deal.financials.remove(year)
    await db.flush()
    return _financials_out(deal)


async def compare_deals(db: AsyncSession, user_id: str, worst, best) -> list[DealComparisonOut]:
    deals = (await db.execute(
        select(Deal).options(selectinload(Deal.financials)).where(Deal.user_id == user_id).order_by(Deal.created_at)
    )).scalars()
    return [compare_deal(deal, deal.financials, worst, best) for deal in deals]
