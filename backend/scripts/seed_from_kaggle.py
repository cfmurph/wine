#!/usr/bin/env python3
"""
Seed the wine app database from the Kaggle Wine Enthusiast dataset.

Dataset: winemag-data-130k-v2.json
Source:  https://www.kaggle.com/datasets/zynicide/wine-reviews

Usage
-----
# From the backend/ directory:
python3 scripts/seed_from_kaggle.py /path/to/winemag-data-130k-v2.json

Options
-------
  --limit N      Only import the first N records (useful for smoke-testing)
  --batch N      DB insert batch size (default 500)
  --dsn URL      Override DATABASE_URL from .env

The script is idempotent: re-running it will update existing rows rather than
create duplicates, using (canonical_name, vintage) as the natural key.
"""

import argparse
import asyncio
import json
import re
import sys
import uuid
from pathlib import Path

# Allow running from backend/ without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.models import Wine, WineScore, WinePrice
from app.db.session import Base


# ---------------------------------------------------------------------------
# Vintage extraction
# ---------------------------------------------------------------------------

_VINTAGE_RE = re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b")


def _extract_vintage(title: str) -> int | None:
    m = _VINTAGE_RE.search(title or "")
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------

def _parse_record(raw: dict) -> dict | None:
    """
    Map one Kaggle record to the internal wine schema.
    Returns None if the record lacks a usable name.
    """
    title: str = (raw.get("title") or "").strip()
    if not title:
        return None

    vintage = _extract_vintage(title)

    # Build canonical_name: strip the vintage year from the title so the
    # name is stable across years (e.g. "Nieto Senetiner Malbec").
    canonical_name = _VINTAGE_RE.sub("", title).strip(" -–—,")
    if not canonical_name:
        canonical_name = title

    # region_1 is the fine-grained wine area (e.g. "Barolo", "Napa Valley")
    # province is the broader area (e.g. "Piedmont", "California")
    # Store province in subregion so searches for broad region names still match.
    region = raw.get("region_1") or ""
    province = raw.get("province") or ""
    subregion = raw.get("region_2") or province  # prefer region_2, fall back to province
    appellation = raw.get("designation") or ""

    # If region_1 is blank, use province as the primary region
    if not region:
        region = province

    grapes = []
    variety = (raw.get("variety") or "").strip()
    if variety:
        grapes = [v.strip() for v in variety.split(",") if v.strip()]

    try:
        price = float(raw["price"]) if raw.get("price") not in (None, "", "null") else None
    except (ValueError, TypeError):
        price = None

    try:
        points = float(raw["points"]) if raw.get("points") not in (None, "", "null") else None
    except (ValueError, TypeError):
        points = None

    return {
        "canonical_name": canonical_name,
        "producer": (raw.get("winery") or "").strip() or None,
        "vintage": vintage,
        "country": (raw.get("country") or "").strip() or None,
        "region": region or None,
        "subregion": subregion or None,
        "appellation": appellation or None,
        "grape_varieties": grapes,
        "style": None,   # dataset doesn't include style; can be inferred later
        "description": (raw.get("description") or "").strip() or None,
        "source_primary": "kaggle_winemag",
        "_price": price,
        "_points": points,
        "_taster": (raw.get("taster_name") or "").strip() or None,
    }


# ---------------------------------------------------------------------------
# Natural key helper
# ---------------------------------------------------------------------------

def _natural_key(record: dict) -> str:
    """Stable string key used for dedup within a single import run."""
    name = (record["canonical_name"] or "").lower()
    vintage = record["vintage"] or 0
    return f"{name}||{vintage}"


# ---------------------------------------------------------------------------
# DB upsert helpers
# ---------------------------------------------------------------------------

async def _upsert_wine(session: AsyncSession, record: dict) -> Wine:
    stmt = select(Wine).where(
        Wine.canonical_name == record["canonical_name"],
        Wine.vintage == record["vintage"],
    )
    result = await session.execute(stmt)
    wine = result.scalar_one_or_none()

    if wine is None:
        wine = Wine(id=str(uuid.uuid4()))
        session.add(wine)

    for field in (
        "canonical_name", "producer", "vintage", "country", "region",
        "subregion", "appellation", "grape_varieties", "description",
        "source_primary",
    ):
        val = record.get(field)
        if val is not None:
            setattr(wine, field, val)

    return wine


async def _upsert_score(session: AsyncSession, wine_id: str, points: float, taster: str | None) -> None:
    provider = "wine_enthusiast"
    stmt = select(WineScore).where(
        WineScore.wine_id == wine_id,
        WineScore.provider == provider,
    )
    result = await session.execute(stmt)
    score = result.scalar_one_or_none()

    if score is None:
        score = WineScore(id=str(uuid.uuid4()), wine_id=wine_id, provider=provider)
        session.add(score)

    score.score = points
    score.score_scale = 100


async def _upsert_price(session: AsyncSession, wine_id: str, price: float) -> None:
    provider = "wine_enthusiast"
    stmt = select(WinePrice).where(
        WinePrice.wine_id == wine_id,
        WinePrice.provider == provider,
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is None:
        existing = WinePrice(id=str(uuid.uuid4()), wine_id=wine_id, provider=provider)
        session.add(existing)

    existing.currency = "USD"
    existing.avg_price = price
    existing.min_price = price
    existing.max_price = price


# ---------------------------------------------------------------------------
# Main import loop
# ---------------------------------------------------------------------------

async def seed(json_path: Path, dsn: str, limit: int | None, batch_size: int) -> None:
    engine = create_async_engine(dsn, echo=False, pool_pre_ping=True)

    # Ensure tables exist (safe no-op if already migrated via Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    print(f"Loading {json_path} …")
    with open(json_path, "r", encoding="utf-8") as f:
        raw_records = json.load(f)

    # Handle both list-of-objects and dict-of-objects formats
    if isinstance(raw_records, dict):
        raw_records = list(raw_records.values())

    if limit:
        raw_records = raw_records[:limit]

    total = len(raw_records)
    print(f"  {total:,} records to process")

    # Parse + deduplicate within this file (keep highest-scoring duplicate)
    seen: dict[str, dict] = {}
    skipped = 0
    for raw in raw_records:
        parsed = _parse_record(raw)
        if parsed is None:
            skipped += 1
            continue
        key = _natural_key(parsed)
        existing = seen.get(key)
        if existing is None:
            seen[key] = parsed
        else:
            # Keep the record with the higher score
            ep = existing.get("_points") or 0
            pp = parsed.get("_points") or 0
            if pp > ep:
                seen[key] = parsed

    records = list(seen.values())
    print(f"  {skipped:,} skipped (no title), {total - skipped - len(records):,} deduped → {len(records):,} unique wines")

    imported = 0
    errors = 0

    for batch_start in range(0, len(records), batch_size):
        batch = records[batch_start : batch_start + batch_size]
        async with Session() as session:
            async with session.begin():
                for record in batch:
                    try:
                        wine = await _upsert_wine(session, record)
                        await session.flush()

                        if record.get("_points") is not None:
                            await _upsert_score(session, wine.id, record["_points"], record.get("_taster"))

                        if record.get("_price") is not None:
                            await _upsert_price(session, wine.id, record["_price"])

                        imported += 1
                    except Exception as exc:
                        errors += 1
                        if errors <= 5:
                            print(f"  [warn] {exc} — skipping record: {record.get('canonical_name')}")

        pct = (batch_start + len(batch)) / len(records) * 100
        print(f"  {batch_start + len(batch):>7,} / {len(records):,}  ({pct:.0f}%)", end="\r", flush=True)

    print(f"\nDone. {imported:,} wines upserted, {errors:,} errors.")
    await engine.dispose()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed wine DB from Kaggle Wine Enthusiast JSON")
    parser.add_argument("json_file", type=Path, help="Path to winemag-data-130k-v2.json")
    parser.add_argument("--limit", type=int, default=None, help="Only import first N records")
    parser.add_argument("--batch", type=int, default=500, help="DB batch size (default 500)")
    parser.add_argument("--dsn", type=str, default=None, help="Override DATABASE_URL")
    args = parser.parse_args()

    if not args.json_file.exists():
        print(f"File not found: {args.json_file}", file=sys.stderr)
        sys.exit(1)

    # Resolve DSN: CLI flag > .env file > default local dev value
    dsn = args.dsn
    if not dsn:
        try:
            from app.core.config import get_settings
            dsn = get_settings().DATABASE_URL
        except Exception:
            dsn = "postgresql+asyncpg://postgres:postgres@localhost:5432/wineapp"

    print(f"Target DB: {dsn.split('@')[-1]}")  # hide credentials in output
    asyncio.run(seed(args.json_file, dsn, args.limit, args.batch))


if __name__ == "__main__":
    main()
