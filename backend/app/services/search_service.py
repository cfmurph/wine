"""
Search service — orchestrates wine search across providers and the internal DB.
"""

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wine import Wine, WineScore, WinePrice
from app.adapters.wine_searcher import WineSearcherAdapter
from app.schemas.wine import WineSearchResult, WineSearchResponse
from app.services.wine_service import upsert_wine
from app.core.logging import logger


async def search_wines(
    db: AsyncSession,
    query: str,
    filters: dict,
    page: int = 1,
    per_page: int = 20,
) -> WineSearchResponse:
    # 1. Check internal DB first
    db_results = await _db_search(db, query, filters, page, per_page)
    if db_results:
        results = [_to_search_result(w) for w in db_results]
        total = await _db_count(db, query, filters)
        logger.info("search_from_db", query=query, count=len(results))
        return WineSearchResponse(results=results, total=total, page=page, per_page=per_page)

    # 2. Fall back to external provider
    adapter = WineSearcherAdapter()
    try:
        raw_wines = await adapter.search_wines(query, {**filters, "page": page, "per_page": per_page})
    except Exception as exc:
        logger.error("search_provider_failure", error=str(exc))
        raw_wines = []
    finally:
        await adapter.aclose()

    saved = []
    for raw in raw_wines:
        try:
            wine = await upsert_wine(db, raw)
            saved.append(wine)
        except Exception as exc:
            logger.warning("upsert_wine_error", error=str(exc))

    results = [_to_search_result(w) for w in saved]
    return WineSearchResponse(results=results, total=len(results), page=page, per_page=per_page)


async def _db_search(
    db: AsyncSession, query: str, filters: dict, page: int, per_page: int
) -> list[Wine]:
    stmt = select(Wine)
    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Wine.canonical_name.ilike(pattern),
                Wine.producer.ilike(pattern),
            )
        )
    stmt = _apply_filters(stmt, filters)
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _db_count(db: AsyncSession, query: str, filters: dict) -> int:
    stmt = select(func.count()).select_from(Wine)
    if query:
        pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Wine.canonical_name.ilike(pattern),
                Wine.producer.ilike(pattern),
            )
        )
    stmt = _apply_filters(stmt, filters)
    result = await db.execute(stmt)
    return result.scalar() or 0


def _apply_filters(stmt, filters: dict):
    if filters.get("region"):
        stmt = stmt.where(Wine.region.ilike(f"%{filters['region']}%"))
    if filters.get("country"):
        stmt = stmt.where(Wine.country.ilike(f"%{filters['country']}%"))
    if filters.get("vintage"):
        stmt = stmt.where(Wine.vintage == int(filters["vintage"]))
    if filters.get("style"):
        stmt = stmt.where(Wine.style.ilike(f"%{filters['style']}%"))
    if filters.get("grape"):
        stmt = stmt.where(Wine.grape_varieties.cast(str).ilike(f"%{filters['grape']}%"))
    return stmt


def _to_search_result(wine: Wine) -> WineSearchResult:
    avg_score = None
    avg_price = None
    currency = "USD"

    if wine.scores:
        scores = [s.score for s in wine.scores if s.score is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

    if wine.prices:
        prices = [p.avg_price for p in wine.prices if p.avg_price is not None]
        avg_price = round(sum(prices) / len(prices), 2) if prices else None
        currency = wine.prices[0].currency if wine.prices else "USD"

    return WineSearchResult(
        id=wine.id,
        canonical_name=wine.canonical_name,
        producer=wine.producer,
        vintage=wine.vintage,
        country=wine.country,
        region=wine.region,
        style=wine.style,
        avg_score=avg_score,
        avg_price=avg_price,
        currency=currency,
        image_url=wine.image_url,
    )
