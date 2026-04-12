from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.wine import WineSearchResponse, WineDetail, WineCompareRequest, WineCompareResponse, WineCompareItem
from app.services.search_service import search_wines
from app.services.wine_service import get_wine_detail, enrich_wine_scores, enrich_wine_pairings, get_wine_by_id

router = APIRouter(prefix="/wines", tags=["wines"])


@router.get("/search", response_model=WineSearchResponse)
async def search(
    q: str = Query("", description="Wine name, producer, or keyword"),
    region: str | None = Query(None),
    country: str | None = Query(None),
    vintage: int | None = Query(None),
    style: str | None = Query(None),
    grape: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    filters = {
        k: v for k, v in {
            "region": region, "country": country, "vintage": vintage,
            "style": style, "grape": grape,
        }.items() if v is not None
    }
    return await search_wines(db, q, filters, page=page, per_page=per_page)


@router.get("/{wine_id}", response_model=WineDetail)
async def get_wine(
    wine_id: str,
    enrich: bool = Query(False, description="Trigger live provider enrichment"),
    db: AsyncSession = Depends(get_db),
):
    if enrich:
        wine = await get_wine_by_id(db, wine_id)
        if wine:
            await enrich_wine_scores(db, wine)
            await enrich_wine_pairings(db, wine)

    detail = await get_wine_detail(db, wine_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return detail


@router.get("/{wine_id}/scores")
async def get_scores(wine_id: str, db: AsyncSession = Depends(get_db)):
    wine = await get_wine_by_id(db, wine_id)
    if wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return {"wine_id": wine_id, "scores": [
        {"provider": s.provider, "score": s.score, "score_scale": s.score_scale, "review_count": s.review_count}
        for s in wine.scores
    ]}


@router.get("/{wine_id}/prices")
async def get_prices(wine_id: str, db: AsyncSession = Depends(get_db)):
    wine = await get_wine_by_id(db, wine_id)
    if wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return {"wine_id": wine_id, "prices": [
        {
            "provider": p.provider, "currency": p.currency,
            "min_price": p.min_price, "avg_price": p.avg_price,
            "max_price": p.max_price, "purchase_url": p.purchase_url,
        }
        for p in wine.prices
    ]}


@router.post("/compare", response_model=WineCompareResponse)
async def compare_wines(payload: WineCompareRequest, db: AsyncSession = Depends(get_db)):
    items: list[WineCompareItem] = []
    for wine_id in payload.wine_ids:
        wine = await get_wine_by_id(db, wine_id)
        if wine is None:
            raise HTTPException(status_code=404, detail=f"Wine {wine_id} not found")

        scores = [s.score for s in wine.scores if s.score is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None
        prices_list = [p.avg_price for p in wine.prices if p.avg_price is not None]
        avg_price = round(sum(prices_list) / len(prices_list), 2) if prices_list else None
        currency = wine.prices[0].currency if wine.prices else "USD"

        value_score = None
        if avg_score and avg_price and avg_price > 0:
            value_score = round(avg_score / avg_price, 2)

        items.append(WineCompareItem(
            id=wine.id,
            canonical_name=wine.canonical_name,
            producer=wine.producer,
            vintage=wine.vintage,
            country=wine.country,
            region=wine.region,
            grape_varieties=wine.grape_varieties or [],
            style=wine.style,
            avg_score=avg_score,
            avg_price=avg_price,
            currency=currency,
            value_score=value_score,
        ))

    return WineCompareResponse(wines=items)
