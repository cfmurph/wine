"""Minimal data for the browser checks in CI, using winery names from the committed listings.

Run with: docker compose exec -T backend python3 - < e2e/seed_fixture.py
Refuses to run if the database already has wineries.
"""

import asyncio
import subprocess
import sys
from datetime import date

sys.path.insert(0, "/app")

from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.models import Wine, Winery, WineryLandCheck

WINERIES = [
    ("Averill Creek Vineyard", "301822", "Duncan"),
    ("Black Dog Cellars", "305021", "Okanagan Falls"),
    ("HAINLE VINEYARDS ESTATE WINERY", "167884", "Peachland"),
    ("Lakeside Cellars", "307635", "Osoyoos"),
    ("Maverick Estate Winery", "304618", "Oliver"),
    ("Millstone Estate Winery", "304224", "Nanaimo"),
    ("Mission Hill Winery", "300228", "West Kelowna"),
    ("Rigour & Whimsy", "310909", "Okanagan Falls"),
    ("S'milka Vista Vineyards", "310045", "Cawston"),
    ("Sage Hills Winery and Vineyards", "305534", "Summerland"),
    ("Seven Stones Winery", "301662", "Cawston"),
    ("The Vibrant Vine", "303633", "Kelowna"),
    ("vinAmite Cellars Inc.", "306100", "Oliver"),
]

LAND_CHECKS = {
    "Seven Stones Winery": dict(
        address_reliable=True, in_alr=True, wells_nearby=9, irrigation_wells_nearby=4,
        fires_since_2000=9, latest_fire_year=2019, largest_fire_hectares=19225.5,
    ),
    "Millstone Estate Winery": dict(
        address_reliable=True, in_alr=True, wells_nearby=12, irrigation_wells_nearby=0, fires_since_2000=0,
    ),
    "Lakeside Cellars": dict(address_reliable=False),
}


async def seed() -> None:
    async with AsyncSessionLocal() as session, session.begin():
        if await session.scalar(select(func.count()).select_from(Winery)):
            raise SystemExit("Refusing to seed: this database already has wineries.")
        wineries = {}
        for name, licence, city in WINERIES:
            wineries[name] = Winery(name=name, licence_number=licence, city=city, region="Okanagan Valley")
            session.add(wineries[name])
        await session.flush()
        for name, fields in LAND_CHECKS.items():
            session.add(WineryLandCheck(winery_id=wineries[name].id, checked_on=date(2026, 11, 1), **fields))
        session.add(Wine(canonical_name="Fixture Pinot Noir", producer="Fixture Cellars", country="Canada", region="British Columbia"))


asyncio.run(seed())
for script in ("import_listings", "import_sales", "link_wineries"):
    subprocess.run([sys.executable, f"/app/scripts/{script}.py"], check=True, cwd="/app")
