"""
Wine service — upsert, fetch, and enrich wine records.
"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wine, WineScore, WinePrice, Pairing
from app.adapters.wine_searcher import WineSearcherAdapter
from app.adapters.global_wine_score import GlobalWineScoreAdapter
from app.adapters.spoonacular import SpoonacularAdapter
from app.schemas.wine import WineDetail
from app.core.logging import logger


async def get_wine_by_id(db: AsyncSession, wine_id: str) -> Wine | None:
    stmt = (
        select(Wine)
        .where(Wine.id == wine_id)
        .options(
            selectinload(Wine.scores),
            selectinload(Wine.prices),
            selectinload(Wine.pairings),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_wine_detail(db: AsyncSession, wine_id: str) -> WineDetail | None:
    wine = await get_wine_by_id(db, wine_id)
    if wine is None:
        return None
    return _to_wine_detail(wine)


async def upsert_wine(db: AsyncSession, raw: dict) -> Wine:
    """Create or update a Wine record from a normalized raw dict."""
    wine_searcher_id = raw.get("wine_searcher_id")
    wine: Wine | None = None

    if wine_searcher_id:
        stmt = select(Wine).where(Wine.wine_searcher_id == wine_searcher_id)
        result = await db.execute(stmt)
        wine = result.scalar_one_or_none()

    if wine is None:
        wine = Wine()
        db.add(wine)

    for field in (
        "canonical_name", "producer", "vintage", "country", "region",
        "subregion", "appellation", "grape_varieties", "style", "abv",
        "description", "image_url", "source_primary", "wine_searcher_id",
        "global_wine_score_id",
    ):
        if raw.get(field) is not None:
            setattr(wine, field, raw[field])

    await db.flush()
    return wine


async def upsert_score(db: AsyncSession, wine_id: str, raw: dict) -> WineScore:
    provider = raw.get("provider", "unknown")
    stmt = select(WineScore).where(
        WineScore.wine_id == wine_id,
        WineScore.provider == provider,
    )
    result = await db.execute(stmt)
    score = result.scalar_one_or_none()

    if score is None:
        score = WineScore(wine_id=wine_id, provider=provider)
        db.add(score)

    score.score = raw.get("score")
    score.score_scale = raw.get("score_scale", 100)
    score.review_count = raw.get("review_count")
    await db.flush()
    return score


async def upsert_price(db: AsyncSession, wine_id: str, raw: dict) -> WinePrice:
    provider = raw.get("provider", "wine_searcher")
    stmt = select(WinePrice).where(
        WinePrice.wine_id == wine_id,
        WinePrice.provider == provider,
    )
    result = await db.execute(stmt)
    price = result.scalar_one_or_none()

    if price is None:
        price = WinePrice(wine_id=wine_id, provider=provider)
        db.add(price)

    price.currency = raw.get("currency", "USD")
    price.min_price = raw.get("min_price")
    price.avg_price = raw.get("avg_price")
    price.max_price = raw.get("max_price")
    price.purchase_url = raw.get("purchase_url")
    await db.flush()
    return price


async def enrich_wine_scores(db: AsyncSession, wine: Wine) -> None:
    """Fetch and store Global Wine Score data for a wine."""
    adapter = GlobalWineScoreAdapter()
    try:
        raw_scores = await adapter.get_scores_for_wine(wine.canonical_name, wine.vintage)
        for raw in raw_scores:
            await upsert_score(db, wine.id, raw)
    except Exception as exc:
        logger.warning("enrich_scores_error", wine_id=wine.id, error=str(exc))
    finally:
        await adapter.aclose()


async def enrich_wine_pairings(db: AsyncSession, wine: Wine) -> None:
    """Fetch and store Spoonacular pairing data for a wine."""
    if not wine.style:
        return
    adapter = SpoonacularAdapter()
    try:
        dishes = await adapter.get_dish_pairing_for_wine(wine.style.lower())
        for dish in dishes:
            stmt = select(Pairing).where(
                Pairing.wine_id == wine.id,
                Pairing.food_name == dish,
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing is None:
                db.add(Pairing(wine_id=wine.id, food_name=dish, provider="spoonacular"))
        await db.flush()
    except Exception as exc:
        logger.warning("enrich_pairings_error", wine_id=wine.id, error=str(exc))
    finally:
        await adapter.aclose()


def _to_wine_detail(wine: Wine) -> WineDetail:
    return WineDetail(
        id=wine.id,
        canonical_name=wine.canonical_name,
        producer=wine.producer,
        vintage=wine.vintage,
        country=wine.country,
        region=wine.region,
        subregion=wine.subregion,
        appellation=wine.appellation,
        grape_varieties=wine.grape_varieties or [],
        style=wine.style,
        abv=wine.abv,
        description=wine.description,
        image_url=wine.image_url,
        scores=[
            {"provider": s.provider, "score": s.score, "score_scale": s.score_scale, "review_count": s.review_count}
            for s in wine.scores
        ],
        prices=[
            {
                "provider": p.provider,
                "currency": p.currency,
                "min_price": p.min_price,
                "avg_price": p.avg_price,
                "max_price": p.max_price,
                "purchase_url": p.purchase_url,
            }
            for p in wine.prices
        ],
        pairings=[p.food_name for p in wine.pairings],
        created_at=wine.created_at,
        updated_at=wine.updated_at,
    )
