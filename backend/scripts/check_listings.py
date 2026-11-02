#!/usr/bin/env python3
"""
Report whether each open listing's source page still loads and shows the recorded price.

Usage (from backend/):
    python3 scripts/check_listings.py [--file listings.csv]

Makes one request per page, respects robots.txt, and reports blocked pages without trying to get
around them. A found price doesn't confirm a listing is still for sale, and page text is never saved.
"""

import argparse
import csv
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts._import_common import DATA_DIR

_USER_AGENT = "WineApp-listing-check/1.0"
_TIMEOUT_SECONDS = 20
_DELAY_SECONDS = 2
_CLOSED_STATUSES = {"Sold", "Sale approved", "Withdrawn"}


def price_appears(text: str, price: float) -> bool:
    """Look for the exact price, written with or without separators, or as $3.25M."""
    value = int(price)
    digits = str(value)
    separated = re.sub(r"(?<=\d)(?=(\d{3})+$)", "[,  ]?", digits)
    patterns = [rf"(?<![\d,.]){separated}(?![\d])"]
    if value % 10_000 == 0:
        millions = f"{value / 1_000_000:.2f}".rstrip("0").rstrip(".")
        patterns.append(rf"(?<![\d.]){re.escape(millions)}\s?(?:M\b|million\b)")
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def classify_page(status: int, text: str, price: float | None) -> str:
    if status in (401, 403, 429):
        return "blocked"
    if status in (404, 410):
        return "page gone"
    if status != 200:
        return f"error {status}"
    if price is None:
        return "loaded, no price to compare"
    return "price found" if price_appears(text, price) else "price not found"


def latest_open_listings(rows: list[dict]) -> list[dict]:
    newest: dict[str, dict] = {}
    for row in sorted(rows, key=lambda r: r["as_of"]):
        newest[row["advertised_name"]] = row
    return [r for r in newest.values() if r["status"] not in _CLOSED_STATUSES]


def _allowed_by_robots(url: str) -> bool:
    parts = urlsplit(url)
    robots = urllib.robotparser.RobotFileParser(f"{parts.scheme}://{parts.netloc}/robots.txt")
    try:
        request = urllib.request.Request(robots.url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            robots.parse(response.read().decode("utf-8", "ignore").splitlines())
    except urllib.error.HTTPError as error:
        # As robotparser does: no file means allowed, access denied means disallowed.
        return error.code not in (401, 403)
    except OSError:
        return True
    return robots.can_fetch(_USER_AGENT, url)


def check(row: dict) -> str:
    url = row.get("source_url")
    if not url:
        return "no source"
    if not _allowed_by_robots(url):
        return "robots.txt disallows"
    price = float(row["asking_price"]) if row.get("asking_price") else None
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return classify_page(response.status, response.read().decode("utf-8", "ignore"), price)
    except urllib.error.HTTPError as error:
        return classify_page(error.code, "", price)
    except OSError:
        return "unreachable"


def main(file: Path) -> None:
    with open(file, encoding="utf-8", newline="") as f:
        listings = latest_open_listings(list(csv.DictReader(f)))
    for index, row in enumerate(listings):
        if index:
            time.sleep(_DELAY_SECONDS)
        print(f"{check(row):28} {row['as_of']}  {row['advertised_name']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DATA_DIR / "winery_listings.csv")
    main(parser.parse_args().file)
