"""Unit tests for provider adapters (no network calls — all mocked)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.adapters.wine_searcher import WineSearcherAdapter
from app.adapters.global_wine_score import GlobalWineScoreAdapter
from app.adapters.spoonacular import SpoonacularAdapter


# ---- WineSearcherAdapter ----

class TestWineSearcherNormalize:
    def test_normalize_wine_basic(self):
        adapter = WineSearcherAdapter.__new__(WineSearcherAdapter)
        raw = {
            "id": "ws-001",
            "name": "Barolo Albe",
            "producer": "G.D. Vajra",
            "vintage": 2019,
            "country": "Italy",
            "region": "Piedmont",
            "grapes": ["Nebbiolo"],
            "type": "Red",
            "alcohol": 14.0,
        }
        result = adapter._normalize_wine(raw)
        assert result["wine_searcher_id"] == "ws-001"
        assert result["canonical_name"] == "Barolo Albe"
        assert result["producer"] == "G.D. Vajra"
        assert result["vintage"] == 2019
        assert result["country"] == "Italy"
        assert result["region"] == "Piedmont"
        assert result["grape_varieties"] == ["Nebbiolo"]
        assert result["style"] == "Red"
        assert result["abv"] == 14.0
        assert result["source_primary"] == "wine_searcher"

    def test_normalize_wine_missing_fields(self):
        adapter = WineSearcherAdapter.__new__(WineSearcherAdapter)
        result = adapter._normalize_wine({"id": "x", "wine_name": "Mystery Wine"})
        assert result["canonical_name"] == "Mystery Wine"
        assert result["producer"] == ""
        assert result["vintage"] is None

    def test_normalize_prices(self):
        adapter = WineSearcherAdapter.__new__(WineSearcherAdapter)
        raw = {"currency": "EUR", "min_price": 40.0, "avg_price": 55.0, "max_price": 70.0}
        result = adapter._normalize_prices(raw)
        assert result["provider"] == "wine_searcher"
        assert result["currency"] == "EUR"
        assert result["min_price"] == 40.0
        assert result["avg_price"] == 55.0

    @pytest.mark.asyncio
    async def test_search_wines_returns_empty_on_http_error(self):
        adapter = WineSearcherAdapter.__new__(WineSearcherAdapter)
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 429
        adapter._client = AsyncMock()
        adapter._client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("rate limit", request=MagicMock(), response=mock_response)
        )
        result = await adapter.search_wines("barolo", {})
        assert result == []


# ---- GlobalWineScoreAdapter ----

class TestGlobalWineScoreNormalize:
    def test_normalize_score(self):
        adapter = GlobalWineScoreAdapter.__new__(GlobalWineScoreAdapter)
        raw = {
            "wine_id": "gws-42",
            "wine": "Barolo Albe",
            "vintage": 2019,
            "globalwinescore": 93.5,
            "nb_reviews": 12,
            "confidence_index": "A",
        }
        result = adapter._normalize(raw)
        assert result["provider"] == "global_wine_score"
        assert result["global_wine_score_id"] == "gws-42"
        assert result["score"] == 93.5
        assert result["score_scale"] == 100
        assert result["review_count"] == 12

    def test_normalize_missing_score(self):
        adapter = GlobalWineScoreAdapter.__new__(GlobalWineScoreAdapter)
        result = adapter._normalize({"wine_id": "1", "wine": "Unknown"})
        assert result["score"] is None
        assert result["vintage"] is None


# ---- SpoonacularAdapter ----

class TestSpoonacularAdapter:
    def test_normalize_product(self):
        adapter = SpoonacularAdapter.__new__(SpoonacularAdapter)
        raw = {
            "title": "Meiomi Pinot Noir",
            "imageUrl": "https://example.com/img.jpg",
            "price": 18.99,
            "averageRating": 0.87,
            "description": "A smooth California Pinot Noir",
            "link": "https://example.com/buy",
        }
        result = adapter._normalize_product(raw)
        assert result["canonical_name"] == "Meiomi Pinot Noir"
        assert result["avg_price"] == 18.99
        assert result["avg_score"] == pytest.approx(87.0)
        assert result["purchase_url"] == "https://example.com/buy"

    @pytest.mark.asyncio
    async def test_get_wine_pairing_returns_fallback_on_error(self):
        adapter = SpoonacularAdapter.__new__(SpoonacularAdapter)
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 402
        adapter._client = AsyncMock()
        adapter._client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("payment required", request=MagicMock(), response=mock_response)
        )
        result = await adapter.get_wine_pairing("steak")
        assert result["wine_types"] == []
        assert result["product_matches"] == []
