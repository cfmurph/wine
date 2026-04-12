"""
Global Wine Score adapter.

API docs: https://www.globalwinescore.com/api/v1/
Authentication: Token-based (Authorization: Token <key>)
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


class GlobalWineScoreAdapter:
    """Adapter for the Global Wine Score API."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.GLOBAL_WINE_SCORE_BASE_URL,
            timeout=10.0,
            headers={
                "Accept": "application/json",
                "Authorization": f"Token {settings.GLOBAL_WINE_SCORE_API_KEY}",
            },
        )

    @retry(**_RETRY_POLICY)
    async def search_wines(self, query: str, filters: dict) -> list[dict]:
        params: dict = {"wine": query}
        if filters.get("vintage"):
            params["vintage"] = filters["vintage"]
        params["page"] = filters.get("page", 1)

        try:
            response = await self._client.get("/globalwinescores/", params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("gws_search_error", status=exc.response.status_code, query=query)
            return []

        return [self._normalize(r) for r in data.get("results", [])]

    @retry(**_RETRY_POLICY)
    async def get_wine_detail(self, external_id: str) -> dict:
        """Not directly supported; use search to enrich a wine."""
        return {}

    @retry(**_RETRY_POLICY)
    async def get_prices(self, external_id: str) -> dict:
        """Global Wine Score does not provide pricing data."""
        return {}

    async def get_scores_for_wine(self, wine_name: str, vintage: int | None = None) -> list[dict]:
        """Fetch critic-aggregated scores for a wine name."""
        filters: dict = {}
        if vintage:
            filters["vintage"] = vintage
        return await self.search_wines(wine_name, filters)

    def _normalize(self, raw: dict) -> dict:
        return {
            "provider": "global_wine_score",
            "global_wine_score_id": str(raw.get("wine_id", "")),
            "canonical_name": raw.get("wine", ""),
            "vintage": raw.get("vintage"),
            "score": raw.get("globalwinescore"),
            "score_scale": 100,
            "review_count": raw.get("nb_reviews"),
            "confidence_index": raw.get("confidence_index"),
        }

    async def aclose(self) -> None:
        await self._client.aclose()
