#!/usr/bin/env python3
"""
Link BC wines and listings to licensed wineries, and write uncertain matches to a review file.

Usage (from backend/), after the import scripts:
    python3 scripts/link_wineries.py [--dsn URL]

To confirm a match, add it to data/winery_aliases.csv and run this again.
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._import_common import DATA_DIR, make_session, resolve_dsn

from sqlalchemy import and_, or_, select

from app.models.wine import Wine, Winery, WineryListing
from app.services.winery_matching import WineryMatcher

REVIEW_FILE = DATA_DIR / "winery_match_review.csv"
_WINEMAG_BC_REGIONS = ("Okanagan Valley", "Similkameen Valley", "British Columbia")


def load_aliases(path: Path) -> dict[str, str]:
    with open(path, encoding="utf-8", newline="") as f:
        return {row["producer"]: row["licence_number"] for row in csv.DictReader(f)}


async def run(dsn: str) -> None:
    engine, Session = make_session(dsn)
    async with Session() as session, session.begin():
        wineries = list((await session.execute(select(Winery))).scalars())
        ids = {w.licence_number: w.id for w in wineries}
        matcher = WineryMatcher(
            [(w.licence_number, w.name, w.licensee) for w in wineries],
            load_aliases(DATA_DIR / "winery_aliases.csv"),
        )

        wines = (await session.execute(select(Wine).where(or_(
            Wine.bc_sku.is_not(None),
            and_(Wine.country == "Canada", Wine.region.in_(_WINEMAG_BC_REGIONS)),
        )))).scalars()

        producers: dict[str, dict] = {}
        for wine in wines:
            match = matcher.match(wine.producer)
            wine.winery_id = ids.get(match.licence_number)
            wine.winery_match_status = match.status
            entry = producers.setdefault(
                wine.producer or "", {"match": match, "wines": 0, "kind": "wine producer"}
            )
            entry["wines"] += 1

        listings = (await session.execute(select(WineryListing))).scalars()
        for listing in listings:
            match = matcher.match(listing.advertised_name)
            listing.winery_id = ids.get(match.licence_number)
            producers[listing.advertised_name] = {"match": match, "wines": 0, "kind": "listing"}

    counts: dict[str, int] = {}
    for entry in producers.values():
        counts[entry["match"].status] = counts.get(entry["match"].status, 0) + 1

    with open(REVIEW_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["kind", "name", "wine_rows", "status", "reason", "candidates"])
        unresolved = [(n, e) for n, e in producers.items() if e["match"].status in ("review", "unmatched") and n]
        for name, entry in sorted(unresolved, key=lambda item: (item[1]["match"].status, -item[1]["wines"], item[0])):
            match = entry["match"]
            writer.writerow([entry["kind"], name, entry["wines"], match.status, match.reason, match.candidate or ""])

    print(f"Names by match status: {counts}. Review file: {REVIEW_FILE}")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn")
    args = parser.parse_args()
    asyncio.run(run(resolve_dsn(args.dsn)))
