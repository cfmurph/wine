"""Unit tests for winery screening scores (no DB required)."""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

import pytest

from app.services.winery_scoring import (
    DEFAULT_WEIGHTS, PeerContext, SubScore, build_peer_context, overall_score, price_per_planted_acre,
    score_brand, score_land, score_operations, score_tourism, score_winery,
)
from app.services.winery_service import _matches_filters, bucket_prices, latest_listings, listings_due_for_recheck


@dataclass
class _Snapshot:
    price: float
    litres: float = 0.75
    observed_on: date = date(2026, 7, 1)


@dataclass
class _Score:
    score: Optional[float]


@dataclass
class _Wine:
    price_snapshots: List[_Snapshot] = field(default_factory=list)
    scores: List[_Score] = field(default_factory=list)


@dataclass
class _Listing:
    asking_price: Optional[float] = None
    planted_acres: Optional[float] = None
    capacity_cases: Optional[int] = None
    includes_licence: Optional[bool] = None
    includes_brand: Optional[bool] = None
    includes_inventory: Optional[bool] = None
    includes_equipment: Optional[bool] = None
    as_of: date = date(2026, 10, 1)
    status: Optional[str] = "Advertised"


@dataclass
class _Winery:
    wines: List[_Wine] = field(default_factory=list)
    listings: List[_Listing] = field(default_factory=list)
    endorsements: Optional[list] = None
    service_capacity: Optional[int] = None
    case_production: Optional[int] = None
    vineyard_acres: Optional[float] = None


def _empty_scores():
    return score_winery(_Winery(), PeerContext())


class TestMissingData:
    def test_no_data_is_unknown_not_zero(self):
        for sub_score in _empty_scores().values():
            assert sub_score.score is None
            assert sub_score.available == 0

    def test_overall_is_unknown_with_no_data(self):
        assert overall_score(_empty_scores(), DEFAULT_WEIGHTS) is None

    def test_missing_component_is_left_out_of_the_average(self):
        winery = _Winery(wines=[_Wine(scores=[_Score(90)])])
        brand = score_brand(winery, PeerContext())
        assert brand.score == 50
        assert (brand.available, brand.total) == (1, 3)

    def test_unknown_sub_score_doesnt_lower_overall(self):
        scores = {"brand": SubScore(80), "tourism": SubScore(60), "land": SubScore(None)}
        assert overall_score(scores, DEFAULT_WEIGHTS) == 70

    def test_one_known_area_is_too_little_for_an_overall_score(self):
        assert overall_score({"tourism": SubScore(100), "land": SubScore(None)}, DEFAULT_WEIGHTS) is None

    def test_stated_exclusion_is_different_from_not_stated(self):
        stated = _Winery(listings=[_Listing(includes_licence=False)])
        unstated = _Winery(listings=[_Listing()])
        assert score_operations(stated).components[1].score == 0
        assert score_operations(unstated).components[1].score is None

    def test_inclusions_name_what_the_listing_doesnt_state(self):
        winery = _Winery(listings=[_Listing(includes_inventory=True, includes_equipment=True)])
        component = score_operations(winery).components[1]
        assert component.score == 100
        assert component.detail == "Included: inventory, equipment. Not stated: licence, brand."


class TestWeights:
    SCORES = {"brand": SubScore(100), "land": SubScore(0)}

    def test_equal_weights_average(self):
        assert overall_score(self.SCORES, {"brand": 1, "land": 1}) == 50

    def test_weights_shift_the_result(self):
        assert overall_score(self.SCORES, {"brand": 3, "land": 1}) == 75

    def test_all_zero_weights_are_unknown(self):
        assert overall_score(self.SCORES, {"brand": 0, "land": 0}) is None


class TestSubScores:
    def test_price_position_uses_only_latest_standard_bottles(self):
        wine = _Wine(price_snapshots=[
            _Snapshot(100, observed_on=date(2026, 1, 1)),
            _Snapshot(25, observed_on=date(2026, 7, 1)),
        ])
        half_bottle = _Wine(price_snapshots=[_Snapshot(500, litres=0.375)])
        brand = score_brand(_Winery(wines=[wine, half_bottle]), PeerContext(median_bottle_price=25))
        assert brand.components[2].score == pytest.approx(33.3)
        assert brand.components[1].score == 20  # both products count toward retail presence

    def test_scales_are_capped(self):
        winery = _Winery(service_capacity=1000, case_production=500_000, vineyard_acres=500)
        assert score_tourism(winery).components[0].score == 100
        assert score_operations(winery).components[0].score == 100
        assert score_land(winery, PeerContext()).components[0].score == 100

    def test_empty_endorsements_are_a_known_zero(self):
        assert score_tourism(_Winery(endorsements=[])).components[1].score == 0

    def test_endorsements_score_by_share(self):
        winery = _Winery(endorsements=["Lounge Area Endorsement", "Picnic Area Endorsement"])
        component = score_tourism(winery).components[1]
        assert component.score == 50
        assert component.detail == "Lounge Area, Picnic Area"

    def test_production_prefers_actual_over_stated_capacity(self):
        winery = _Winery(case_production=2_000, listings=[_Listing(capacity_cases=10_000)])
        assert score_operations(winery).components[0].detail == "2,000 cases produced"

    def test_stated_capacity_is_labelled_as_capacity(self):
        winery = _Winery(listings=[_Listing(capacity_cases=5_000)])
        assert score_operations(winery).components[0].detail == "5,000 cases of stated capacity"

    def test_price_per_acre_at_median_scores_fifty(self):
        winery = _Winery(listings=[_Listing(asking_price=3_000_000, planted_acres=6)])
        assert price_per_planted_acre(winery) == 500_000
        land = score_land(winery, PeerContext(median_price_per_planted_acre=500_000))
        assert land.components[1].score == 50

    def test_latest_listing_is_used(self):
        winery = _Winery(listings=[
            _Listing(asking_price=9, planted_acres=1, as_of=date(2025, 1, 1)),
            _Listing(asking_price=4, planted_acres=1, as_of=date(2026, 1, 1)),
        ])
        assert price_per_planted_acre(winery) == 4


def test_peer_context_medians():
    wineries = [
        _Winery(wines=[_Wine(price_snapshots=[_Snapshot(20)]), _Wine(price_snapshots=[_Snapshot(40)])]),
        _Winery(listings=[_Listing(asking_price=100, planted_acres=2)]),
    ]
    peers = build_peer_context(wineries)
    assert peers.median_bottle_price == 30
    assert peers.median_price_per_planted_acre == 50
    assert build_peer_context([]).median_bottle_price is None


def test_price_buckets_cover_every_price_once():
    buckets = bucket_prices([10, 15, 24.99, 25, 60, 500])
    assert sum(b.count for b in buckets) == 6
    assert buckets[0].count == 1
    assert buckets[-1].label == "$60+"
    assert buckets[-1].count == 2


@pytest.mark.parametrize(
    "status,expected",
    [("Advertised", True), ("Offer accepted", True), ("Sold", False), ("Sale approved", False), ("Withdrawn", False), (None, False)],
)
def test_for_sale_filter_hides_closed_listings(status, expected):
    summary = {"name": "Test", "city": None, "region": None, "asking_price": None, "production_cases": None, "listing_status": status}
    assert _matches_filters(summary, None, None, True, None, None, None) is expected


def test_latest_listings_keeps_newest_row_in_given_order():
    @dataclass
    class _Row:
        advertised_name: str
        as_of: date

    old = _Row("Maverick", date(2026, 10, 1))
    new = _Row("Maverick", date(2026, 11, 1))
    other = _Row("Hainle", date(2026, 10, 1))
    assert latest_listings([other, old, new]) == [other, new]


def test_recheck_lists_open_old_listings_oldest_first():
    @dataclass
    class _Row:
        status: str
        as_of: date

    today = date(2026, 11, 1)
    older = _Row("Advertised", date(2026, 8, 1))
    old = _Row("Offer accepted", date(2026, 10, 1))
    fresh = _Row("Advertised", date(2026, 10, 15))
    sold = _Row("Sold", date(2026, 1, 1))
    assert listings_due_for_recheck([fresh, old, sold, older], today) == [older, old]


@pytest.mark.parametrize("status", ["Sold", "Sale approved", "Withdrawn"])
def test_closed_listing_doesnt_score_sale_terms(status):
    listing = _Listing(asking_price=1_000_000, planted_acres=10, includes_licence=True, status=status)
    winery = _Winery(listings=[listing])
    assert price_per_planted_acre(winery) is None
    land = score_land(winery, PeerContext(None, 100_000))
    assert next(c for c in land.components if c.label == "Asking price per planted acre").score is None
    assert next(c for c in land.components if c.label == "Planted acres").score is not None
    assert next(c for c in score_operations(winery).components if c.label == "Included in sale").score is None


def test_open_listing_still_scores_sale_terms():
    winery = _Winery(listings=[_Listing(asking_price=1_000_000, planted_acres=10, status="Offer accepted")])
    assert price_per_planted_acre(winery) == 100_000


def test_newer_closed_row_overrides_older_open_row():
    old = _Listing(asking_price=1_000_000, planted_acres=10, as_of=date(2026, 10, 1))
    sold = _Listing(asking_price=1_000_000, planted_acres=10, as_of=date(2026, 11, 1), status="Sold")
    assert price_per_planted_acre(_Winery(listings=[old, sold])) is None
