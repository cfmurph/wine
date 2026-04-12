"""
Pairing service — uses Spoonacular to answer food → wine and wine → food queries.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.spoonacular import SpoonacularAdapter
from app.schemas.wine import PairingSearchResponse, WineSearchResult
from app.core.logging import logger


async def get_pairings_for_food(
    db: AsyncSession,
    food: str,
) -> PairingSearchResponse:
    adapter = SpoonacularAdapter()
    try:
        result = await adapter.get_wine_pairing(food)
        wine_types = result.get("wine_types", [])
        product_matches = result.get("product_matches", [])
    except Exception as exc:
        logger.error("pairing_service_error", food=food, error=str(exc))
        wine_types = []
        product_matches = []
    finally:
        await adapter.aclose()

    wines = [
        WineSearchResult(
            id=f"spoonacular_{i}",
            canonical_name=p.get("canonical_name", p.get("title", "")),
            image_url=p.get("image_url", p.get("imageUrl")),
            avg_price=p.get("avg_price"),
            avg_score=p.get("avg_score"),
        )
        for i, p in enumerate(product_matches)
    ]

    return PairingSearchResponse(
        food=food,
        wine_types=wine_types,
        wines=wines,
        provider="spoonacular",
    )
