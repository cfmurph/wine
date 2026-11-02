"""Unit tests for service-layer helpers (no DB required)."""

import pytest
from dataclasses import dataclass, field
from typing import Optional, List

from app.services.search_service import _to_search_result


@dataclass
class _FakeScore:
    provider: str = "global_wine_score"
    score: Optional[float] = None
    score_scale: int = 100
    review_count: Optional[int] = None


@dataclass
class _FakePrice:
    provider: str = "wine_searcher"
    currency: str = "USD"
    min_price: Optional[float] = None
    avg_price: Optional[float] = None
    max_price: Optional[float] = None
    purchase_url: Optional[str] = None


@dataclass
class _FakeWine:
    id: str = "wine-1"
    canonical_name: str = "Test Wine"
    producer: str = "Test Producer"
    vintage: Optional[int] = 2020
    country: str = "France"
    region: str = "Bordeaux"
    style: str = "Red"
    image_url: Optional[str] = None
    scores: List[_FakeScore] = field(default_factory=list)
    prices: List[_FakePrice] = field(default_factory=list)


class TestToSearchResult:
    def test_basic_no_scores_no_prices(self):
        wine = _FakeWine()
        result = _to_search_result(wine)  # type: ignore[arg-type]
        assert result.id == "wine-1"
        assert result.canonical_name == "Test Wine"
        assert result.avg_score is None
        assert result.avg_price is None
        assert result.currency == "USD"

    def test_avg_score_computed(self):
        wine = _FakeWine(scores=[_FakeScore(score=90.0), _FakeScore(score=94.0)])
        result = _to_search_result(wine)  # type: ignore[arg-type]
        assert result.avg_score == 92.0

    def test_avg_price_computed(self):
        wine = _FakeWine(prices=[_FakePrice(avg_price=50.0), _FakePrice(avg_price=60.0)])
        result = _to_search_result(wine)  # type: ignore[arg-type]
        assert result.avg_price == 55.0

    def test_currency_taken_from_first_price(self):
        wine = _FakeWine(prices=[_FakePrice(avg_price=45.0, currency="EUR")])
        result = _to_search_result(wine)  # type: ignore[arg-type]
        assert result.currency == "EUR"

    def test_none_scores_ignored(self):
        wine = _FakeWine(scores=[_FakeScore(score=None), _FakeScore(score=88.0)])
        result = _to_search_result(wine)  # type: ignore[arg-type]
        assert result.avg_score == 88.0


def test_settings_ignore_unknown_variables(monkeypatch):
    # A setting removed from the code but left in someone's .env must not stop the app starting.
    from app.core.config import Settings

    monkeypatch.setenv("REDIS_URL", "redis://old:6379/0")
    assert not hasattr(Settings(), "REDIS_URL")


_DEPLOYED = {
    "ENVIRONMENT": "production",
    "SECRET_KEY": "x" * 40,
    "DATABASE_URL": "postgresql+asyncpg://app:real-password@db:5432/wine",
    "CORS_ORIGINS": "https://wine.example.com",
    "DEBUG": False,
}


def _settings(**overrides):
    from app.core.config import Settings

    return Settings(_env_file=None, **{**_DEPLOYED, **overrides})


def test_safe_deployed_settings_are_accepted():
    settings = _settings(CORS_ORIGINS="https://a.example.com, https://b.example.com")
    assert settings.cors_origin_list == ["https://a.example.com", "https://b.example.com"]


@pytest.mark.parametrize(
    "unsafe",
    [
        {"SECRET_KEY": "change-me-in-production"},
        {"SECRET_KEY": "short"},
        {"DEBUG": True},
        {"DATABASE_URL": "postgresql+asyncpg://postgres:postgres@db:5432/wine"},
        {"DATABASE_URL": "postgresql+asyncpg://app:pw@localhost:5432/wine"},
        {"CORS_ORIGINS": "*"},
        {"CORS_ORIGINS": ""},
    ],
)
@pytest.mark.parametrize("environment", ["staging", "production"])
def test_deployed_environments_refuse_unsafe_settings(environment, unsafe):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        _settings(ENVIRONMENT=environment, **unsafe)


def test_development_keeps_working_defaults():
    from app.core.config import Settings

    settings = Settings(_env_file=None, ENVIRONMENT="development")
    assert settings.SECRET_KEY
    assert settings.cors_origin_list == ["http://localhost:3000"]
