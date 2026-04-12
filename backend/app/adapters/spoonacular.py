"""
Spoonacular adapter for wine pairing and recommendation endpoints.

API docs: https://spoonacular.com/food-api/docs#Wine-Guide
Authentication: apiKey query param
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

_RETRY_POLICY = dict(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)


class SpoonacularAdapter:
    """Adapter for the Spoonacular Wine API endpoints."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.SPOONACULAR_BASE_URL,
            timeout=10.0,
            headers={"Accept": "application/json"},
        )

    def _params(self, extra: dict | None = None) -> dict:
        p = {"apiKey": settings.SPOONACULAR_API_KEY}
        if extra:
            p.update(extra)
        return p

    # WineProviderAdapter protocol stubs (Spoonacular is pairing-only)
    async def search_wines(self, query: str, filters: dict) -> list[dict]:
        return []

    async def get_wine_detail(self, external_id: str) -> dict:
        return {}

    async def get_prices(self, external_id: str) -> dict:
        return {}

    @retry(**_RETRY_POLICY)
    async def get_wine_pairing(self, food: str) -> dict:
        """
        Returns wine types that pair well with the given food,
        plus a text description and a product recommendation.
        """
        try:
            response = await self._client.get(
                "/food/wine/pairing",
                params=self._params({"food": food}),
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("spoonacular_pairing_error", status=exc.response.status_code, food=food)
            return {"wine_types": [], "pairing_text": "", "product_matches": []}

        return {
            "wine_types": data.get("pairedWines", []),
            "pairing_text": data.get("pairingText", ""),
            "product_matches": data.get("productMatches", []),
        }

    @retry(**_RETRY_POLICY)
    async def get_wine_recommendation(self, wine_type: str, max_price: float | None = None) -> list[dict]:
        """Return product recommendations for a given wine type."""
        params: dict = {"wine": wine_type, "number": 5}
        if max_price:
            params["maxPrice"] = max_price

        try:
            response = await self._client.get(
                "/food/wine/recommendation",
                params=self._params(params),
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("spoonacular_recommendation_error", status=exc.response.status_code, wine=wine_type)
            return []

        return [self._normalize_product(p) for p in data.get("recommendedWines", [])]

    @retry(**_RETRY_POLICY)
    async def get_dish_pairing_for_wine(self, wine_type: str) -> list[str]:
        """Return dishes that pair well with a given wine type."""
        try:
            response = await self._client.get(
                "/food/wine/dishes",
                params=self._params({"wine": wine_type}),
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("spoonacular_dishes_error", status=exc.response.status_code, wine=wine_type)
            return []

        return data.get("pairings", [])

    def _normalize_product(self, raw: dict) -> dict:
        return {
            "canonical_name": raw.get("title", ""),
            "image_url": raw.get("imageUrl", ""),
            "avg_price": raw.get("price"),
            "avg_score": raw.get("averageRating", 0) * 100 if raw.get("averageRating") else None,
            "description": raw.get("description", ""),
            "purchase_url": raw.get("link", ""),
        }

    async def aclose(self) -> None:
        await self._client.aclose()
