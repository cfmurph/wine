"""Deal tracker: each user's private purchase pipeline. Every query filters by user."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.wine import Deal, DealItem, Winery
from app.schemas.deal import DealCreate, DealItemCreate, DealItemUpdate, DealUpdate

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
