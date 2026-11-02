#!/usr/bin/env python3
"""
Import annual wine sales for BC and Canada from Statistics Canada table 10-10-0010-01.

Usage (from backend/):
    python3 scripts/import_market_stats.py [--file 10100010-eng.zip] [--dsn URL]

Idempotent: rows are upserted by source, period, geography, category and metric.
"""

import argparse
import asyncio
import csv
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._import_common import make_session, read_source, resolve_dsn

from sqlalchemy import select

from app.models.wine import MarketStat

SOURCE = "statcan_10_10_0010"
URL = "https://www150.statcan.gc.ca/n1/en/tbl/csv/10100010-eng.zip"
_GEOGRAPHIES = {"British Columbia", "Canada"}
_METRICS = {"Value for total sales": "value", "Volume for total sales": "volume"}
_SCALES = {"thousands": 1_000, "units": 1}


def parse_rows(rows) -> list[dict]:
    records = []
    for row in rows:
        metric = _METRICS.get(row["Value, volume and absolute volume"])
        if (
            metric is None
            or row["GEO"] not in _GEOGRAPHIES
            or row["Type of beverage"] != "Wines"
            or row["Type of sales"] != "Total sales"
            or not row["VALUE"]
        ):
            continue
        records.append({
            "period": row["REF_DATE"],
            "geography": row["GEO"],
            "category": "Wines",
            "metric": metric,
            "value": float(row["VALUE"]) * _SCALES[row["SCALAR_FACTOR"]],
            "unit": row["UOM"],
        })
    return records


async def run(file: Path | None, dsn: str) -> None:
    archive = zipfile.ZipFile(io.BytesIO(read_source(file, URL)))
    name = next(n for n in archive.namelist() if "MetaData" not in n)
    records = parse_rows(csv.DictReader(io.StringIO(archive.read(name).decode("utf-8-sig"))))

    engine, Session = make_session(dsn)
    async with Session() as session, session.begin():
        stmt = select(MarketStat).where(MarketStat.source == SOURCE)
        existing = {(s.period, s.geography, s.category, s.metric): s for s in (await session.execute(stmt)).scalars()}
        for record in records:
            stat = existing.get((record["period"], record["geography"], record["category"], record["metric"]))
            if stat is None:
                session.add(MarketStat(source=SOURCE, **record))
            else:
                stat.value, stat.unit = record["value"], record["unit"]
    print(f"{len(records):,} market stats upserted")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--dsn")
    args = parser.parse_args()
    asyncio.run(run(args.file, resolve_dsn(args.dsn)))
