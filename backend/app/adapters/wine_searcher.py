"""
Wine-Searcher adapter.

Wine-Searcher API docs: https://api.wine-searcher.com
Authentication: API key passed as a query parameter or header (see your plan).
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


class WineSearcherAdapter:
    """Adapter for the Wine-Searcher REST API."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.WINE_SEARCHER_BASE_URL,
            timeout=10.0,
            headers={"Accept": "application/json"},
        )

    async def _get(self, path: str, params: dict) -> dict:
        params = {**params, "api_key": settings.WINE_SEARCHER_API_KEY}
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    @retry(**_RETRY_POLICY)
    async def search_wines(self, query: str, filters: dict) -> list[dict]:
        params: dict = {"q": query}
        if filters.get("region"):
            params["region"] = filters["region"]
        if filters.get("country"):
            params["country"] = filters["country"]
        if filters.get("vintage"):
            params["vintage"] = filters["vintage"]
        if filters.get("grape"):
            params["grape"] = filters["grape"]
        page = filters.get("page", 1)
        per_page = filters.get("per_page", 20)
        params["page"] = page
        params["per_page"] = per_page

        try:
            data = await self._get("/search", params)
        except httpx.HTTPStatusError as exc:
            logger.warning("wine_searcher_search_error", status=exc.response.status_code, query=query)
            return []

        wines = data.get("wines", data.get("results", []))
        return [self._normalize_wine(w) for w in wines]

    @retry(**_RETRY_POLICY)
    async def get_wine_detail(self, external_id: str) -> dict:
        try:
            data = await self._get(f"/wine/{external_id}", {})
        except httpx.HTTPStatusError as exc:
            logger.warning("wine_searcher_detail_error", status=exc.response.status_code, id=external_id)
            return {}
        return self._normalize_wine(data)

    @retry(**_RETRY_POLICY)
    async def get_prices(self, external_id: str) -> dict:
        try:
            data = await self._get(f"/wine/{external_id}/prices", {})
        except httpx.HTTPStatusError as exc:
            logger.warning("wine_searcher_prices_error", status=exc.response.status_code, id=external_id)
            return {}
        return self._normalize_prices(data)

    # --- Field mapping ---------------------------------------------------------

    def _normalize_wine(self, raw: dict) -> dict:
        """Map Wine-Searcher fields → internal schema fields."""
        return {
            "wine_searcher_id": str(raw.get("id", "")),
            "canonical_name": raw.get("name", raw.get("wine_name", "")),
            "producer": raw.get("producer", raw.get("winery", "")),
            "vintage": raw.get("vintage") or raw.get("year"),
            "country": raw.get("country", ""),
            "region": raw.get("region", ""),
            "subregion": raw.get("subregion", ""),
            "appellation": raw.get("appellation", ""),
            "grape_varieties": raw.get("grapes", raw.get("grape_varieties", [])),
            "style": raw.get("type", raw.get("wine_type", "")),
            "abv": raw.get("alcohol", raw.get("abv")),
            "description": raw.get("description", ""),
            "image_url": raw.get("image", raw.get("image_url", "")),
            "source_primary": "wine_searcher",
        }

    def _normalize_prices(self, raw: dict) -> dict:
        return {
            "provider": "wine_searcher",
            "currency": raw.get("currency", "USD"),
            "min_price": raw.get("min_price"),
            "avg_price": raw.get("avg_price") or raw.get("price"),
            "max_price": raw.get("max_price"),
            "purchase_url": raw.get("purchase_url", ""),
        }

    async def aclose(self) -> None:
        await self._client.aclose()
