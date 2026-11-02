#!/usr/bin/env python3
"""
Import licensed BC wineries from the BC government's licensed establishments workbook.

Usage (from backend/):
    python3 scripts/import_bc_wineries.py [--file workbook.xlsx] [--dsn URL]

Idempotent: rows are upserted by licence number. Licence categories count meaderies
and fruit wineries as wineries, and the file doesn't separate them from grape wineries.
"""

import argparse
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._import_common import make_session, read_source, read_xlsx, resolve_dsn

from sqlalchemy import select

from app.models.wine import Winery
from app.services.winery_matching import clean_establishment_name

SOURCE = "bc_licensed_establishments"
URL = (
    "https://www2.gov.bc.ca/assets/gov/employment-business-and-economic-development/"
    "business-management/liquor-regulation-licensing/reports/all_liquor_licensed_establishments_in_bc.xlsx"
)
_LICENCE_KEY = "Licence Number (Licence) (Licence)"

# A rough grouping by licence address, not the official Geographical Indications.
_REGION_CITIES = {
    "Okanagan": [
        "OLIVER", "PENTICTON", "KELOWNA", "SUMMERLAND", "OKANAGAN FALLS", "WEST KELOWNA", "NARAMATA",
        "OSOYOOS", "LAKE COUNTRY", "KALEDEN", "VERNON", "PEACHLAND", "SPALLUMCHEEN",
    ],
    "Similkameen": ["CAWSTON", "KEREMEOS"],
    "Fraser Valley & Metro Vancouver": [
        "LANGLEY", "ABBOTSFORD", "RICHMOND", "VANCOUVER", "SURREY", "DELTA", "AGASSIZ", "ALDERGROVE",
        "CHILLIWACK", "DEWDNEY", "LINDELL BEACH", "NORTH VANCOUVER", "PITT MEADOWS", "PORT COQUITLAM", "PORT MOODY",
    ],
    "Vancouver Island": [
        "COBBLE HILL", "DUNCAN", "COURTENAY", "NANAIMO", "VICTORIA", "COMOX", "MILL BAY", "NORTH SAANICH",
        "BLACK CREEK", "BRENTWOOD BAY", "CENTRAL SAANICH", "COWICHAN BAY", "ERRINGTON", "NORTH COWICHAN",
        "PORT ALBERNI", "SAANICHTON",
    ],
    "Gulf & Discovery Islands": [
        "SALT SPRING ISLAND", "HORNBY ISLAND", "DENMAN ISLAND", "PENDER ISLAND", "GABRIOLA ISLAND",
        "SATURNA ISLAND", "THETIS ISLAND", "LASQUETI ISLAND", "MANSONS LANDING", "QUADRA ISLAND",
    ],
    "Shuswap": ["SALMON ARM", "TAPPEN", "CELISTA", "GRINDROD", "ENDERBY"],
    "Thompson": ["KAMLOOPS", "MONTE CREEK", "LOGAN LAKE"],
    "Lillooet": ["LILLOOET"],
    "Kootenays": ["CRESTON", "WYNNDEL", "CASTLEGAR", "NAKUSP", "TRAIL", "BURTON"],
}
CITY_REGIONS = {city: region for region, cities in _REGION_CITIES.items() for city in cities}


def _excel_date(serial: str | None) -> date | None:
    try:
        return date(1899, 12, 30) + timedelta(days=int(float(serial)))
    except (TypeError, ValueError):
        return None


def parse_wineries(sheets: dict[str, list[dict]]) -> list[dict]:
    """Combine the licence, service area and endorsement sheets into one record per winery."""
    by_name = {name.lower(): rows for name, rows in sheets.items()}
    licences = next(rows for name, rows in by_name.items() if name.startswith("liquor web stats"))

    capacities: dict[str, int] = {}
    for row in by_name.get("service areas", []):
        try:
            capacity = int(float(row.get("Capacity")))
        except (TypeError, ValueError):
            continue
        capacities[row.get(_LICENCE_KEY)] = capacities.get(row.get(_LICENCE_KEY), 0) + capacity

    endorsements: dict[str, set[str]] = {}
    for row in by_name.get("endorsements", []):
        if row.get("Name"):
            endorsements.setdefault(row.get(_LICENCE_KEY), set()).add(row["Name"])

    records = []
    for row in licences:
        if row.get("Licence Sub Category Id") != "Winery":
            continue
        licence_number = row["Licence Number"]
        city = (row.get("Establishment Address City") or "").strip()
        records.append({
            "licence_number": licence_number,
            "name": clean_establishment_name(row.get("Establishment")),
            "licensee": row.get("Licensee"),
            "street": row.get("Establishment Address Street"),
            "city": city.title() or None,
            "local_government": row.get("LG / IN"),
            "postal_code": row.get("Establishment Address Postal Code"),
            "region": CITY_REGIONS.get(city.upper()),
            "licence_expiry": _excel_date(row.get("Expiry Date")),
            "service_capacity": capacities.get(licence_number),
            "endorsements": sorted(endorsements.get(licence_number, set())),
        })
    return records


async def run(file: Path | None, dsn: str) -> None:
    records = parse_wineries(read_xlsx(read_source(file, URL)))
    engine, Session = make_session(dsn)
    async with Session() as session, session.begin():
        existing = {w.licence_number: w for w in (await session.execute(select(Winery))).scalars()}
        for record in records:
            winery = existing.get(record["licence_number"])
            if winery is None:
                winery = Winery(licence_number=record["licence_number"], province="British Columbia")
                session.add(winery)
            for field, value in record.items():
                setattr(winery, field, value)
            winery.source = SOURCE
            winery.source_date = date.today()
    print(f"{len(records):,} wineries upserted, {sum(1 for r in records if not r['region'])} without a mapped region")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--dsn")
    args = parser.parse_args()
    asyncio.run(run(args.file, resolve_dsn(args.dsn)))
