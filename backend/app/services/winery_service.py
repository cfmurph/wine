from datetime import date
from statistics import median

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.wine import MarketStat, PriceSnapshot, Wine, Winery, WineryListing, WinerySale
from app.schemas.winery import (
    DataSourceOut, MarketResponse, MarketStatOut, PriceBucketOut, WineryDetail,
    WineryListingOut, WineryListResponse, WinerySaleOut, WinerySummary, WineryWineOut,
)
from app.services.winery_scoring import (
    STANDARD_BOTTLE_LITRES, PeerContext, bottle_prices, build_peer_context, critic_scores,
    current_listing, latest_snapshot, overall_score, production_cases, score_winery,
)

_CLOSED_LISTING_STATUSES = {"Sold", "Sale approved", "Withdrawn"}
RECHECK_AFTER_DAYS = 30

_LICENCE_SOURCE = DataSourceOut(
    label="BC licensed establishments workbook",
    url="https://www2.gov.bc.ca/gov/content?id=6D2A8A0AC8C64BECB9B1C2AD7FB33006",
)
_PRICE_SOURCE = DataSourceOut(
    label="BC Liquor Store price list (shelf prices, not sales)",
    url="https://catalogue.data.gov.bc.ca/dataset/e43be180-7511-4e6f-84d3-ad6c9f5c3e2b",
)
_CRITIC_SOURCE = DataSourceOut(
    label="Wine Enthusiast reviews via Kaggle (historical, USD)",
    as_of="2019 file",
    url="https://www.kaggle.com/datasets/zynicide/wine-reviews",
)
_STATS_SOURCE = DataSourceOut(
    label="Statistics Canada table 10-10-0010-01 (market totals, not any one winery)",
    url="https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1010001001",
)
_MARKET_REPORTS = [
    DataSourceOut(
        label="BCLDB Liquor Market Review (quarterly PDFs, wholesale sales)",
        url="https://www.bcldb.com/publications/liquor-market-review",
    ),
    DataSourceOut(
        label="BC Wine Grape Acreage Report 2025 (PDF)",
        url="https://www2.gov.bc.ca/assets/gov/farming-natural-resources-and-industry/agriculture-and-seafood/animal-and-crops/crop-production/2025-grape-acreage-and-production-report.pdf",
    ),
]
_PRICE_BUCKETS = [(0, 15), (15, 20), (20, 25), (25, 30), (30, 40), (40, 60), (60, None)]


async def _load_wineries(db: AsyncSession) -> list[Winery]:
    stmt = select(Winery).order_by(Winery.name).options(
        selectinload(Winery.wines).selectinload(Wine.scores),
        selectinload(Winery.wines).selectinload(Wine.price_snapshots),
        selectinload(Winery.wines).selectinload(Wine.prices),
        selectinload(Winery.listings),
        selectinload(Winery.land_check),
    )
    return list((await db.execute(stmt)).scalars().all())


def _summary_fields(winery: Winery, peers: PeerContext, weights: dict[str, float]) -> dict:
    prices = bottle_prices(winery)
    scores = critic_scores(winery)
    listing = current_listing(winery)
    sub_scores = score_winery(winery, peers)
    return {
        "id": winery.id,
        "name": winery.name,
        "city": winery.city,
        "region": winery.region,
        "wine_count": len(winery.wines),
        "median_bottle_price": round(median(prices), 2) if prices else None,
        "avg_critic_score": round(sum(scores) / len(scores), 1) if scores else None,
        "production_cases": production_cases(winery)[0],
        "asking_price": listing.asking_price if listing else None,
        "listing_status": listing.status if listing else None,
        "overall_score": overall_score(sub_scores, weights),
        "sub_scores": {name: _sub_score_out(s) for name, s in sub_scores.items()},
    }


def _sub_score_out(sub_score) -> dict:
    return {
        "score": sub_score.score,
        "available": sub_score.available,
        "total": sub_score.total,
        "components": sub_score.components,
    }


def _matches_filters(summary: dict, q, region, for_sale, min_asking, max_asking, min_cases) -> bool:
    asking = summary["asking_price"]
    cases = summary["production_cases"]
    if q and q.lower() not in f"{summary['name']} {summary['city'] or ''}".lower():
        return False
    if region and summary["region"] != region:
        return False
    if for_sale and (summary["listing_status"] is None or summary["listing_status"] in _CLOSED_LISTING_STATUSES):
        return False
    if min_asking is not None and (asking is None or asking < min_asking):
        return False
    if max_asking is not None and (asking is None or asking > max_asking):
        return False
    if min_cases is not None and (cases is None or cases < min_cases):
        return False
    return True


def latest_listings(listings) -> list:
    """Keep each listing's newest row, in the given order. Older rows are its history."""
    newest = {l.advertised_name: l for l in sorted(listings, key=lambda l: l.as_of)}
    return [l for l in listings if newest[l.advertised_name] is l]


def listings_due_for_recheck(listings, today: date) -> list:
    """Open listings last checked too long ago, oldest first. Expects each listing's newest row."""
    due = [
        l for l in listings
        if l.status not in _CLOSED_LISTING_STATUSES and (today - l.as_of).days >= RECHECK_AFTER_DAYS
    ]
    return sorted(due, key=lambda l: l.as_of)


async def list_wineries(
    db: AsyncSession,
    weights: dict[str, float],
    q: str | None = None,
    region: str | None = None,
    for_sale: bool = False,
    min_asking: float | None = None,
    max_asking: float | None = None,
    min_cases: int | None = None,
) -> WineryListResponse:
    # A few hundred rows: scoring and filtering in memory keeps one definition of each metric.
    wineries = await _load_wineries(db)
    peers = build_peer_context(wineries)
    summaries = [_summary_fields(w, peers, weights) for w in wineries]
    results = [
        WinerySummary(**s) for s in summaries
        if _matches_filters(s, q, region, for_sale, min_asking, max_asking, min_cases)
    ]
    return WineryListResponse(
        results=results,
        total=len(results),
        regions=sorted({w.region for w in wineries if w.region}),
    )


def _wine_out(wine: Wine) -> WineryWineOut:
    snapshot = latest_snapshot(wine)
    scores = [s.score for s in wine.scores if s.score is not None]
    usd_prices = [p.avg_price for p in wine.prices if p.currency == "USD" and p.avg_price is not None]
    return WineryWineOut(
        id=wine.id,
        name=wine.canonical_name,
        style=wine.style,
        vintage=wine.vintage,
        retail_price_cad=snapshot.price if snapshot else None,
        litres=snapshot.litres if snapshot else None,
        price_date=snapshot.observed_on if snapshot else None,
        critic_score=max(scores) if scores else None,
        historical_price_usd=usd_prices[0] if usd_prices else None,
    )


def _winery_sources(winery: Winery) -> list[DataSourceOut]:
    sources = [_LICENCE_SOURCE.model_copy(update={
        "as_of": winery.source_date.isoformat() if winery.source_date else None,
    })]
    snapshots = [s for s in map(latest_snapshot, winery.wines) if s]
    if snapshots:
        sources.append(_PRICE_SOURCE.model_copy(update={
            "as_of": max(s.observed_on for s in snapshots).isoformat(),
        }))
    if critic_scores(winery):
        sources.append(_CRITIC_SOURCE)
    return sources


def _detail(winery: Winery, peers: PeerContext, weights: dict[str, float]) -> WineryDetail:
    return WineryDetail(
        **_summary_fields(winery, peers, weights),
        land_check=winery.land_check,
        licence_number=winery.licence_number,
        licensee=winery.licensee,
        street=winery.street,
        postal_code=winery.postal_code,
        licence_expiry=winery.licence_expiry,
        endorsements=winery.endorsements or [],
        service_capacity=winery.service_capacity,
        wines=sorted(map(_wine_out, winery.wines), key=lambda w: w.name),
        listings=[
            WineryListingOut.model_validate(l)
            for l in sorted(winery.listings, key=lambda l: l.as_of, reverse=True)
        ],
        sources=_winery_sources(winery),
    )


async def get_wineries(db: AsyncSession, winery_ids: list[str], weights: dict[str, float]) -> list[WineryDetail]:
    """Details in the requested order, skipping unknown ids."""
    wineries = await _load_wineries(db)
    peers = build_peer_context(wineries)
    by_id = {w.id: w for w in wineries}
    return [_detail(by_id[i], peers, weights) for i in winery_ids if i in by_id]


def bucket_prices(prices: list[float]) -> list[PriceBucketOut]:
    buckets = []
    for low, high in _PRICE_BUCKETS:
        label = f"${low}–{high}" if high else f"${low}+"
        count = sum(1 for p in prices if p >= low and (high is None or p < high))
        buckets.append(PriceBucketOut(label=label, count=count))
    return buckets


async def get_market(db: AsyncSession) -> MarketResponse:
    stats = (await db.execute(
        select(MarketStat).order_by(MarketStat.period, MarketStat.geography, MarketStat.metric)
    )).scalars().all()

    latest_date = (await db.execute(
        select(PriceSnapshot.observed_on).order_by(PriceSnapshot.observed_on.desc()).limit(1)
    )).scalar()
    prices = list((await db.execute(
        select(PriceSnapshot.price).where(
            PriceSnapshot.observed_on == latest_date,
            PriceSnapshot.litres == STANDARD_BOTTLE_LITRES,
        )
    )).scalars().all()) if latest_date else []

    listings = (await db.execute(
        select(WineryListing).order_by(WineryListing.asking_price.desc().nulls_last())
    )).scalars().all()

    sales = (await db.execute(
        select(WinerySale).order_by(WinerySale.sold_year.desc(), WinerySale.sale_price.desc())
    )).scalars().all()

    current_listings = latest_listings(listings)

    return MarketResponse(
        stats=[MarketStatOut.model_validate(s) for s in stats],
        stats_source=_STATS_SOURCE,
        price_buckets=bucket_prices(prices),
        median_bottle_price=round(median(prices), 2) if prices else None,
        priced_bottles=len(prices),
        price_date=latest_date,
        price_source=_PRICE_SOURCE,
        listings=[WineryListingOut.model_validate(l) for l in current_listings],
        listings_to_recheck=[
            WineryListingOut.model_validate(l) for l in listings_due_for_recheck(current_listings, date.today())
        ],
        recheck_after_days=RECHECK_AFTER_DAYS,
        sales=[WinerySaleOut.model_validate(s) for s in sales],
        reports=_MARKET_REPORTS,
    )
