#!/usr/bin/env python3
"""
Import BC wines and retail prices from the BC Liquor Store price list (BC Data Catalogue).

Usage (from backend/):
    python3 scripts/import_bc_prices.py [--file list.csv --observed-on 2026-07-01] [--dsn URL]

Idempotent: wines are upserted by SKU and each month adds one price snapshot per wine.
These are shelf prices. The file says nothing about how many bottles sold.
"""

import argparse
import asyncio
import csv
import io
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._import_common import fetch, make_session, resolve_dsn
from scripts.seed_from_kaggle import _extract_vintage

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.wine import PriceSnapshot, Wine

SOURCE = "bc_liquor_price_list"
DATASET_URL = (
    "https://catalogue.data.gov.bc.ca/api/3/action/package_show"
    "?id=e43be180-7511-4e6f-84d3-ad6c9f5c3e2b"
)


def _to_float(value: str | None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_row(row: dict) -> dict | None:
    """Map one price list row to a wine record, or None if it isn't a priced BC wine."""
    price = _to_float(row.get("PRODUCT_PRICE"))
    name = (row.get("PRODUCT_LONG_NAME") or "").strip()
    if (
        row.get("ITEM_CATEGORY_NAME") != "Wine"
        or row.get("ITEM_SUBCATEGORY_NAME") != "Canada - BC"
        or price is None
        or not name
    ):
        return None

    producer, separator, _ = name.partition(" - ")
    style = re.sub(r"^Canada - BC | Wine$", "", row.get("ITEM_CLASS_NAME") or "") or None
    return {
        "sku": row["PRODUCT_SKU_NO"],
        "canonical_name": name.title(),
        "producer": producer.strip().title() if separator else None,
        "vintage": _extract_vintage(name),
        "style": style,
        "abv": _to_float(row.get("PRODUCT_ALCOHOL_PERCENT")),
        "price": price,
        "litres": _to_float(row.get("PRODUCT_LITRES_PER_CONTAINER")),
    }


def observed_on_from_name(name: str) -> date:
    """'..._price_list_july_2026' -> 2026-07-01."""
    match = re.search(r"([a-z]+)[_ ](\d{4})", name.lower())
    if not match:
        raise ValueError(f"No month and year in resource name: {name}")
    return datetime.strptime(f"{match.group(1)} {match.group(2)}", "%B %Y").date()


async def run(file: Path | None, observed_on: date | None, dsn: str) -> None:
    if file:
        if observed_on is None:
            raise SystemExit("--observed-on is required with --file")
        content = file.read_bytes()
    else:
        resource = next(
            r for r in json.loads(fetch(DATASET_URL))["result"]["resources"] if r["format"].lower() == "csv"
        )
        observed_on = observed_on or observed_on_from_name(resource["name"])
        content = fetch(resource["url"])

    rows = csv.DictReader(io.StringIO(content.decode("utf-8-sig", "replace")))
    records = [r for r in map(parse_row, rows) if r]

    engine, Session = make_session(dsn)
    async with Session() as session, session.begin():
        stmt = select(Wine).where(Wine.bc_sku.is_not(None)).options(selectinload(Wine.price_snapshots))
        existing = {w.bc_sku: w for w in (await session.execute(stmt)).scalars()}
        for record in records:
            wine = existing.get(record["sku"])
            if wine is None:
                wine = Wine(
                    bc_sku=record["sku"], canonical_name=record["canonical_name"],
                    country="Canada", subregion="British Columbia", source_primary=SOURCE, price_snapshots=[],
                )
                session.add(wine)
            for field in ("canonical_name", "producer", "vintage", "style", "abv"):
                setattr(wine, field, record[field])

            snapshot = next(
                (s for s in wine.price_snapshots if s.source == SOURCE and s.observed_on == observed_on), None
            )
            if snapshot is None:
                snapshot = PriceSnapshot(source=SOURCE, observed_on=observed_on, currency="CAD", price=record["price"])
                wine.price_snapshots.append(snapshot)
            snapshot.price = record["price"]
            snapshot.litres = record["litres"]
    print(f"{len(records):,} BC wines upserted with prices as of {observed_on}")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--observed-on", type=date.fromisoformat)
    parser.add_argument("--dsn")
    args = parser.parse_args()
    asyncio.run(run(args.file, args.observed_on, resolve_dsn(args.dsn)))
