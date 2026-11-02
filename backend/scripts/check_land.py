#!/usr/bin/env python3
"""
Check public BC map data around each winery that has a sale listing or a tracked deal.

Usage (from backend/):
    python3 scripts/check_land.py [--dsn URL]

Uses the BC Address Geocoder and BC Geographic Warehouse. Results describe the area around an address
point, not the legal parcel. Water rights licences are left out because that dataset is "access only" and
can't be reproduced without permission; check them through the Province's water rights databases.
Contains information licensed under the Open Government Licence - British Columbia.
"""

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._import_common import make_session, resolve_dsn

from sqlalchemy import select

from app.models import Deal, Winery, WineryLandCheck, WineryListing

_GEOCODER = "https://geocoder.api.gov.bc.ca/addresses.json?"
_WFS = "https://openmaps.gov.bc.ca/geo/pub/ows?"
_USER_AGENT = "WineApp-land-check/1.0"
_TIMEOUT_SECONDS = 40
_MIN_GEOCODE_SCORE = 90
_WELL_RADIUS_METRES = 500
_FIRE_RADIUS_METRES = 5000
_FIRST_FIRE_YEAR = 2000
_MAX_FEATURES = 1000


def address_is_reliable(properties: dict) -> bool:
    return properties.get("score", 0) >= _MIN_GEOCODE_SCORE and properties.get("matchPrecision") == "CIVIC_NUMBER"


def parse_alr(rows: list[dict]) -> bool:
    return any(row.get("STATUS") == "ALR" for row in rows)


def summarize_wells(rows: list[dict]) -> tuple[int, int]:
    irrigation = [r for r in rows if "irrigation" in (r.get("INTENDED_WATER_USE") or "").lower()]
    return len(rows), len(irrigation)


def summarize_fires(rows: list[dict]) -> tuple[int, int | None, float | None]:
    years = [r["FIRE_YEAR"] for r in rows if r.get("FIRE_YEAR") is not None]
    sizes = [r["FIRE_SIZE_HECTARES"] for r in rows if r.get("FIRE_SIZE_HECTARES") is not None]
    return len(rows), max(years, default=None), max(sizes, default=None)


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode())


def _layer(layer: str, cql: str, properties: str) -> list[dict] | None:
    """Rows from a map layer, or None if it failed or returned more than was fetched."""
    query = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": layer,
        "outputFormat": "json", "srsName": "EPSG:3005", "count": _MAX_FEATURES,
        "CQL_FILTER": cql, "propertyName": properties,
    }
    try:
        data = _get_json(_WFS + urllib.parse.urlencode(query))
    except (OSError, ValueError) as error:
        print(f"  {layer}: {type(error).__name__}")
        return None
    if data.get("numberMatched", 0) > len(data["features"]):
        print(f"  {layer}: too many results")
        return None
    return [feature["properties"] for feature in data["features"]]


def _check(street: str | None, city: str | None) -> dict:
    empty = {"matched_address": None, "geocode_score": None, "address_reliable": False}
    if not street or not city:
        return empty
    query = urllib.parse.urlencode({"addressString": f"{street}, {city}, BC", "maxResults": 1, "outputSRS": 3005})
    try:
        feature = _get_json(_GEOCODER + query)["features"][0]
    except (OSError, ValueError, IndexError, KeyError) as error:
        print(f"  geocoder: {type(error).__name__}")
        return empty
    properties = feature["properties"]
    result = {
        "matched_address": properties.get("fullAddress"),
        "geocode_score": properties.get("score"),
        "address_reliable": address_is_reliable(properties),
    }
    if not result["address_reliable"]:
        return result

    x, y = feature["geometry"]["coordinates"]
    point = f"SRID=3005;POINT({x} {y})"
    alr = _layer("WHSE_LEGAL_ADMIN_BOUNDARIES.OATS_ALR_POLYS", f"INTERSECTS(GEOMETRY,{point})", "STATUS")
    wells = _layer(
        "WHSE_WATER_MANAGEMENT.GW_WATER_WELLS_WRBC_SVW",
        f"DWITHIN(GEOMETRY,{point},{_WELL_RADIUS_METRES},meters)",
        "WELL_TAG_NUMBER,INTENDED_WATER_USE",
    )
    fires = _layer(
        "WHSE_LAND_AND_NATURAL_RESOURCE.PROT_HISTORICAL_FIRE_POLYS_SP",
        f"DWITHIN(SHAPE,{point},{_FIRE_RADIUS_METRES},meters) AND FIRE_YEAR>={_FIRST_FIRE_YEAR}",
        "FIRE_YEAR,FIRE_SIZE_HECTARES",
    )
    if alr is not None:
        result["in_alr"] = parse_alr(alr)
    if wells is not None:
        result["wells_nearby"], result["irrigation_wells_nearby"] = summarize_wells(wells)
    if fires is not None:
        result["fires_since_2000"], result["latest_fire_year"], result["largest_fire_hectares"] = summarize_fires(fires)
    return result


_RESULT_FIELDS = (
    "matched_address", "geocode_score", "address_reliable", "in_alr", "wells_nearby",
    "irrigation_wells_nearby", "fires_since_2000", "latest_fire_year", "largest_fire_hectares",
)


async def run(dsn: str) -> None:
    engine, Session = make_session(dsn)
    async with Session() as session, session.begin():
        ids = set((await session.execute(select(WineryListing.winery_id))).scalars())
        ids |= set((await session.execute(select(Deal.winery_id))).scalars())
        ids.discard(None)
        wineries = (await session.execute(select(Winery).where(Winery.id.in_(ids)).order_by(Winery.name))).scalars().all()
        existing = {c.winery_id: c for c in (await session.execute(select(WineryLandCheck))).scalars()}
        for winery in wineries:
            print(winery.name)
            result = _check(winery.street, winery.city)
            check = existing.get(winery.id) or WineryLandCheck(winery_id=winery.id)
            for field in _RESULT_FIELDS:
                setattr(check, field, result.get(field))
            check.checked_on = date.today()
            session.add(check)
    print(f"{len(wineries):,} wineries checked")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn")
    asyncio.run(run(resolve_dsn(parser.parse_args().dsn)))
