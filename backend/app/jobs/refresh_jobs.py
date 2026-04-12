"""
Nightly background jobs for data refresh.
Run these via cron, APScheduler, or a task queue like Celery/ARQ.
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.wine import Wine
from app.services.wine_service import enrich_wine_scores, enrich_wine_pairings, upsert_price
from app.adapters.wine_searcher import WineSearcherAdapter
from app.core.logging import logger


async def refresh_stale_prices(stale_hours: int = 24) -> None:
    """Re-fetch prices for wines whose price data is older than stale_hours."""
    cutoff = datetime.utcnow() - timedelta(hours=stale_hours)
    async with AsyncSessionLocal() as db:
        stmt = select(Wine).where(Wine.updated_at < cutoff).limit(100)
        result = await db.execute(stmt)
        wines = result.scalars().all()
        adapter = WineSearcherAdapter()
        try:
            for wine in wines:
                if not wine.wine_searcher_id:
                    continue
                try:
                    price_data = await adapter.get_prices(wine.wine_searcher_id)
                    if price_data:
                        await upsert_price(db, wine.id, price_data)
                except Exception as exc:
                    logger.warning("refresh_price_error", wine_id=wine.id, error=str(exc))
            await db.commit()
        finally:
            await adapter.aclose()
    logger.info("refresh_stale_prices_complete", count=len(wines))


async def refresh_popular_scores(limit: int = 50) -> None:
    """Re-enrich score data for the most-referenced wines."""
    async with AsyncSessionLocal() as db:
        stmt = select(Wine).limit(limit)
        result = await db.execute(stmt)
        wines = result.scalars().all()
        for wine in wines:
            try:
                await enrich_wine_scores(db, wine)
            except Exception as exc:
                logger.warning("refresh_score_error", wine_id=wine.id, error=str(exc))
        await db.commit()
    logger.info("refresh_popular_scores_complete", count=len(wines))
