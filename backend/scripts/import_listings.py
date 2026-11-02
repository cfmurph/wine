#!/usr/bin/env python3
"""
Import hand-entered winery listings from data/winery_listings.csv.

Usage (from backend/):
    python3 scripts/import_listings.py [--file listings.csv] [--dsn URL]

Idempotent: rows are upserted by advertised name and as-of date. Prices are asking
prices. A blank "includes_*" cell means the listing doesn't say.
"""

import argparse
import asyncio
import csv
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._import_common import DATA_DIR, make_session, resolve_dsn

from sqlalchemy import select

from app.models.wine import WineryListing

_FLOATS = ("asking_price", "previous_asking_price", "total_acres", "planted_acres")
_BOOLEANS = ("includes_licence", "includes_brand", "includes_inventory", "includes_equipment")
_TEXT = ("location", "status", "notes", "source_url")


def parse_row(row: dict) -> dict:
    record = {"advertised_name": row["advertised_name"].strip(), "as_of": date.fromisoformat(row["as_of"])}
    record.update({f: float(row[f]) if row.get(f) else None for f in _FLOATS})
    record["capacity_cases"] = int(row["capacity_cases"]) if row.get("capacity_cases") else None
    record.update({f: row[f].strip().lower() == "true" if row.get(f) else None for f in _BOOLEANS})
    record.update({f: row.get(f) or None for f in _TEXT})
    return record


async def run(file: Path, dsn: str) -> None:
    with open(file, encoding="utf-8", newline="") as f:
        records = [parse_row(row) for row in csv.DictReader(f)]

    engine, Session = make_session(dsn)
    async with Session() as session, session.begin():
        existing = {(l.advertised_name, l.as_of): l for l in (await session.execute(select(WineryListing))).scalars()}
        for record in records:
            listing = existing.get((record["advertised_name"], record["as_of"]))
            if listing is None:
                session.add(WineryListing(currency="CAD", **record))
            else:
                for field, value in record.items():
                    setattr(listing, field, value)
    print(f"{len(records):,} listings upserted")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DATA_DIR / "winery_listings.csv")
    parser.add_argument("--dsn")
    args = parser.parse_args()
    asyncio.run(run(args.file, resolve_dsn(args.dsn)))
