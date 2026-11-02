"""Screening scores for winery acquisition candidates.

Missing data stays None and is left out of an average. It never counts as zero,
so a winery isn't penalised for what public sources don't say about it. Every
scale below is a judgment call, shown to the user alongside the score.
"""

from dataclasses import dataclass, field
from statistics import median

STANDARD_BOTTLE_LITRES = 0.75
CRITIC_SCORE_FLOOR = 80
CRITIC_SCORE_CEILING = 100
FULL_RETAIL_RANGE_SKUS = 10
FULL_PLANTED_ACRES = 20
FULL_SERVICE_CAPACITY = 200
FULL_PRODUCTION_CASES = 10_000
TOURISM_ENDORSEMENTS = 4
DEFAULT_WEIGHTS = {"brand": 1.0, "land": 1.0, "tourism": 1.0, "operations": 1.0}
# One area alone can't rank a winery: a perfect tourism score says nothing about the business.
MIN_KNOWN_SUB_SCORES = 2


@dataclass
class Component:
    label: str
    score: float | None
    detail: str


@dataclass
class SubScore:
    score: float | None
    components: list[Component] = field(default_factory=list)

    @property
    def available(self) -> int:
        return sum(1 for c in self.components if c.score is not None)

    @property
    def total(self) -> int:
        return len(self.components)


def _scaled(ratio: float) -> float:
    return round(max(0.0, min(ratio, 1.0)) * 100, 1)


def _sub_score(components: list[Component]) -> SubScore:
    known = [c.score for c in components if c.score is not None]
    return SubScore(round(sum(known) / len(known), 1) if known else None, components)


def latest_snapshot(wine):
    return max(wine.price_snapshots, key=lambda s: s.observed_on, default=None)


def bottle_prices(winery) -> list[float]:
    """Latest retail price of each standard-size bottle linked to this winery."""
    snapshots = (latest_snapshot(w) for w in winery.wines)
    return [s.price for s in snapshots if s and s.litres == STANDARD_BOTTLE_LITRES]


def critic_scores(winery) -> list[float]:
    return [s.score for w in winery.wines for s in w.scores if s.score is not None]


def current_listing(winery):
    return max(winery.listings, key=lambda l: l.as_of, default=None)


def planted_acres(winery) -> float | None:
    listing = current_listing(winery)
    return winery.vineyard_acres or (listing.planted_acres if listing else None)


def price_per_planted_acre(winery) -> float | None:
    listing = current_listing(winery)
    acres = listing.planted_acres if listing else None
    return listing.asking_price / acres if listing and listing.asking_price and acres else None


def production_cases(winery) -> tuple[int | None, str]:
    if winery.case_production:
        return winery.case_production, "cases produced"
    listing = current_listing(winery)
    if listing and listing.capacity_cases:
        return listing.capacity_cases, "cases of stated capacity"
    return None, ""


@dataclass
class PeerContext:
    """Province-wide benchmarks that a winery is compared against."""
    median_bottle_price: float | None = None
    median_price_per_planted_acre: float | None = None


def build_peer_context(wineries) -> PeerContext:
    prices = [p for w in wineries for p in bottle_prices(w)]
    per_acre = [v for v in map(price_per_planted_acre, wineries) if v]
    return PeerContext(median(prices) if prices else None, median(per_acre) if per_acre else None)


def score_brand(winery, peers: PeerContext) -> SubScore:
    scores = critic_scores(winery)
    critic = Component("Critic scores", None, "No critic scores linked")
    if scores:
        average = sum(scores) / len(scores)
        critic = Component(
            "Critic scores",
            _scaled((average - CRITIC_SCORE_FLOOR) / (CRITIC_SCORE_CEILING - CRITIC_SCORE_FLOOR)),
            f"Average {average:.1f}/100 across {len(scores)} historical reviews",
        )

    # Not appearing in the price list could mean a failed name match, so it stays unknown.
    listed = sum(1 for w in winery.wines if w.price_snapshots)
    retail = Component("Retail presence", None, "No BC Liquor Store products linked")
    if listed:
        retail = Component(
            "Retail presence", _scaled(listed / FULL_RETAIL_RANGE_SKUS), f"{listed} products on the BC Liquor Store list"
        )

    prices = bottle_prices(winery)
    position = Component("Price position", None, "No 750 ml retail prices linked")
    if prices and peers.median_bottle_price:
        winery_median = median(prices)
        # Half the provincial median scores 0, the median about 33, and double the median 100.
        ratio = winery_median / peers.median_bottle_price
        position = Component(
            "Price position",
            _scaled((ratio - 0.5) / 1.5),
            f"Median ${winery_median:.2f} against BC median ${peers.median_bottle_price:.2f}",
        )
    return _sub_score([critic, retail, position])


def score_land(winery, peers: PeerContext) -> SubScore:
    acres = planted_acres(winery)
    planted = Component("Planted acres", None, "Planted acres unknown")
    if acres:
        planted = Component("Planted acres", _scaled(acres / FULL_PLANTED_ACRES), f"{acres:g} planted acres")

    per_acre = price_per_planted_acre(winery)
    value = Component("Asking price per planted acre", None, "Needs an asking price and planted acres")
    if per_acre and peers.median_price_per_planted_acre:
        # Paying the median scores 50. Half the median or less scores 100.
        value = Component(
            "Asking price per planted acre",
            _scaled(peers.median_price_per_planted_acre / per_acre / 2),
            f"${per_acre:,.0f} against listing median ${peers.median_price_per_planted_acre:,.0f}",
        )
    return _sub_score([planted, value])


def score_tourism(winery) -> SubScore:
    capacity = Component("Licensed service capacity", None, "No service areas in the licence file")
    if winery.service_capacity:
        capacity = Component(
            "Licensed service capacity",
            _scaled(winery.service_capacity / FULL_SERVICE_CAPACITY),
            f"{winery.service_capacity} licensed capacity",
        )

    # The licence file is the official record, so an empty list is a real zero.
    endorsements = Component("Hospitality endorsements", None, "Licence data not imported")
    if winery.endorsements is not None:
        names = [e.replace(" Endorsement", "") for e in winery.endorsements]
        endorsements = Component(
            "Hospitality endorsements",
            _scaled(len(names) / TOURISM_ENDORSEMENTS),
            ", ".join(names) or "None on the licence",
        )
    return _sub_score([capacity, endorsements])


def score_operations(winery) -> SubScore:
    cases, unit = production_cases(winery)
    production = Component("Production size", None, "Production unknown")
    if cases:
        production = Component("Production size", _scaled(cases / FULL_PRODUCTION_CASES), f"{cases:,} {unit}")

    listing = current_listing(winery)
    inclusions = Component("Included in sale", None, "No listing states what's included")
    if listing:
        items = {
            "licence": listing.includes_licence,
            "brand": listing.includes_brand,
            "inventory": listing.includes_inventory,
            "equipment": listing.includes_equipment,
        }
        stated = {k: v for k, v in items.items() if v is not None}
        if stated:
            included = [k for k, v in stated.items() if v]
            unstated = [k for k in items if k not in stated]
            inclusions = Component(
                "Included in sale",
                _scaled(len(included) / len(stated)),
                f"Included: {', '.join(included) or 'none stated'}."
                + (f" Not stated: {', '.join(unstated)}." if unstated else ""),
            )
    return _sub_score([production, inclusions])


def score_winery(winery, peers: PeerContext) -> dict[str, SubScore]:
    return {
        "brand": score_brand(winery, peers),
        "land": score_land(winery, peers),
        "tourism": score_tourism(winery),
        "operations": score_operations(winery),
    }


def overall_score(sub_scores: dict[str, SubScore], weights: dict[str, float]) -> float | None:
    """Weighted average of the known sub-scores, or None with too few of them or all weights at zero."""
    known = [(s.score, weights.get(name, 0)) for name, s in sub_scores.items() if s.score is not None]
    total_weight = sum(weight for _, weight in known)
    if len(known) < MIN_KNOWN_SUB_SCORES or not total_weight:
        return None
    return round(sum(score * weight for score, weight in known) / total_weight, 1)
