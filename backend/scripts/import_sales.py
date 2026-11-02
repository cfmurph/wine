#!/usr/bin/env python3
"""
Import hand-entered reported winery sales from data/winery_sales.csv.

Usage (from backend/):
    python3 scripts/import_sales.py [--file sales.csv] [--dsn URL]

Idempotent: rows are upserted by name and year. A blank price or acreage means unknown.
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._import_common import DATA_DIR, make_session, resolve_dsn

from sqlalchemy import select

from app.models import WinerySale

_OPTIONAL_FLOATS = ("last_asking_price", "total_acres", "planted_acres")
_OPTIONAL_TEXT = ("location", "notes", "source_url")


def parse_row(row: dict) -> dict:
    for field in ("name", "sold_year", "sale_price", "sale_type", "evidence"):
        if not row.get(field):
            raise ValueError(f"Sale is missing {field}: {row.get('name')}")
    record = {
        "name": row["name"].strip(),
        "sold_year": int(row["sold_year"]),
        "sale_price": float(row["sale_price"]),
        "sale_type": row["sale_type"],
        "evidence": row["evidence"],
    }
    record.update({f: float(row[f]) if row.get(f) else None for f in _OPTIONAL_FLOATS})
    record.update({f: row.get(f) or None for f in _OPTIONAL_TEXT})
    return record


async def run(file: Path, dsn: str) -> None:
    with open(file, encoding="utf-8", newline="") as f:
        records = [parse_row(row) for row in csv.DictReader(f)]

    engine, Session = make_session(dsn)
    async with Session() as session, session.begin():
        existing = {(s.name, s.sold_year): s for s in (await session.execute(select(WinerySale))).scalars()}
        for record in records:
            sale = existing.get((record["name"], record["sold_year"]))
            if sale is None:
                session.add(WinerySale(**record))
            else:
                for field, value in record.items():
                    setattr(sale, field, value)
    print(f"{len(records):,} sales upserted")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DATA_DIR / "winery_sales.csv")
    parser.add_argument("--dsn")
    args = parser.parse_args()
    asyncio.run(run(args.file, resolve_dsn(args.dsn)))
