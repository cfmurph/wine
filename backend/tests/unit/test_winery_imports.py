"""Unit tests for the winery data import parsers."""

import io
import sys
import zipfile
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts._import_common import read_xlsx
from scripts.import_bc_prices import observed_on_from_name, parse_row as parse_price_row
from scripts.import_bc_wineries import parse_wineries
from scripts.import_listings import parse_row as parse_listing_row
from scripts.import_market_stats import parse_rows as parse_market_rows
from scripts.check_listings import classify_page, latest_open_listings, price_appears
from scripts.import_sales import parse_row as parse_sale_row
from app.schemas.winery import WinerySaleOut

_KEY = "Licence Number (Licence) (Licence)"


def _sheets():
    return {
        "Liquor Web Stats Active Lic...": [
            {
                "Licence Number": "1", "Licence Sub Category Id": "Winery",
                "Establishment": "Test Winery (1)", "Establishment Address City": "OLIVER ",
                "Expiry Date": "46477", "Licensee": "Test Co",
            },
            {"Licence Number": "2", "Licence Sub Category Id": "Distillery", "Establishment": "Still (2)"},
            {
                "Licence Number": "3", "Licence Sub Category Id": "Winery",
                "Establishment": "Far North (3)", "Establishment Address City": "PRINCE GEORGE",
            },
        ],
        "Service Areas": [
            {_KEY: "1", "Capacity": "30"}, {_KEY: "1", "Capacity": "20"}, {_KEY: "1", "Capacity": "n/a"},
        ],
        "Endorsements": [
            {_KEY: "1", "Name": "Picnic Area Endorsement"}, {_KEY: "1", "Name": "Picnic Area Endorsement"},
        ],
    }


class TestParseWineries:
    def test_keeps_only_wineries(self):
        assert [r["licence_number"] for r in parse_wineries(_sheets())] == ["1", "3"]

    def test_combines_sheets_and_cleans_fields(self):
        record = parse_wineries(_sheets())[0]
        assert record["name"] == "Test Winery"
        assert record["city"] == "Oliver"
        assert record["region"] == "Okanagan"
        assert record["licence_expiry"] == date(2027, 3, 31)
        assert record["service_capacity"] == 50
        assert record["endorsements"] == ["Picnic Area Endorsement"]

    def test_unknown_values_stay_unknown(self):
        record = parse_wineries(_sheets())[1]
        assert record["region"] is None
        assert record["service_capacity"] is None
        assert record["licence_expiry"] is None
        assert record["endorsements"] == []


class TestParsePrices:
    ROW = {
        "ITEM_CATEGORY_NAME": "Wine", "ITEM_SUBCATEGORY_NAME": "Canada - BC",
        "ITEM_CLASS_NAME": "Canada - BC Red Wine", "PRODUCT_SKU_NO": "620351",
        "PRODUCT_LONG_NAME": "SANDHILL - SMALL LOTS VANESSA 2017", "PRODUCT_PRICE": "41.99",
        "PRODUCT_LITRES_PER_CONTAINER": "0.75", "PRODUCT_ALCOHOL_PERCENT": "14",
    }

    def test_maps_a_bc_wine(self):
        record = parse_price_row(self.ROW)
        assert record["producer"] == "Sandhill"
        assert record["vintage"] == 2017
        assert record["style"] == "Red"
        assert record["price"] == 41.99
        assert record["litres"] == 0.75

    @pytest.mark.parametrize("change", [
        {"ITEM_CATEGORY_NAME": "Beer"},
        {"ITEM_SUBCATEGORY_NAME": "France Wine"},
        {"PRODUCT_PRICE": ""},
    ])
    def test_skips_other_rows(self, change):
        assert parse_price_row({**self.ROW, **change}) is None

    def test_name_without_separator_has_no_producer(self):
        assert parse_price_row({**self.ROW, "PRODUCT_LONG_NAME": "HOUSE RED"})["producer"] is None

    def test_reads_date_from_resource_name(self):
        assert observed_on_from_name("BC_Liquor_Store_Product_Price_List_July_2026") == date(2026, 7, 1)


class TestParseMarket:
    ROW = {
        "REF_DATE": "2024/2025", "GEO": "British Columbia", "Type of sales": "Total sales",
        "Type of beverage": "Wines", "Value, volume and absolute volume": "Value for total sales",
        "UOM": "Dollars", "SCALAR_FACTOR": "thousands", "VALUE": "890746",
    }

    def test_scales_values(self):
        record = parse_market_rows([self.ROW])[0]
        assert record["value"] == 890_746_000
        assert record["metric"] == "value"

    @pytest.mark.parametrize("change", [
        {"GEO": "Ontario"},
        {"Type of beverage": "Beer"},
        {"Type of sales": "Total per capita sales"},
        {"Value, volume and absolute volume": "Absolute volume for total sales"},
        {"VALUE": ""},
    ])
    def test_skips_other_rows(self, change):
        assert parse_market_rows([{**self.ROW, **change}]) == []


class TestParseListing:
    def test_blank_inclusion_means_not_stated(self):
        record = parse_listing_row({
            "advertised_name": " Test ", "as_of": "2026-10-01", "asking_price": "3100000",
            "includes_licence": "false", "includes_brand": "true", "includes_inventory": "", "capacity_cases": "",
        })
        assert record["advertised_name"] == "Test"
        assert record["asking_price"] == 3_100_000
        assert record["includes_licence"] is False
        assert record["includes_brand"] is True
        assert record["includes_inventory"] is None
        assert record["capacity_cases"] is None


def test_read_xlsx_uses_first_row_as_headers():
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/sharedStrings.xml", f"<sst {ns}><si><t>Name</t></si><si><t>Test</t></si></sst>")
        archive.writestr("xl/workbook.xml", f'<workbook {ns}><sheets><sheet name="One"/></sheets></workbook>')
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            f'<worksheet {ns}><sheetData><row><c r="A1" t="s"><v>0</v></c></row>'
            f'<row><c r="A2" t="s"><v>1</v></c></row></sheetData></worksheet>',
        )
    assert read_xlsx(buffer.getvalue()) == {"One": [{"Name": "Test"}]}


def test_parse_sale_keeps_blanks_unknown():
    row = {
        "name": " Test Winery ", "location": "Oliver", "sold_year": "2025", "sale_price": "2050000",
        "last_asking_price": "", "total_acres": "10.5", "planted_acres": "", "sale_type": "Private sale",
        "evidence": "News article opened", "notes": "", "source_url": "https://example.com",
    }
    record = parse_sale_row(row)
    assert record["name"] == "Test Winery"
    assert record["sold_year"] == 2025
    assert record["sale_price"] == 2050000
    assert record["last_asking_price"] is None
    assert record["planted_acres"] is None
    assert record["notes"] is None


@pytest.mark.parametrize("missing", ["sale_price", "sold_year", "sale_type", "evidence"])
def test_parse_sale_requires_core_fields(missing):
    row = {"name": "A", "sold_year": "2025", "sale_price": "1", "sale_type": "Private sale", "evidence": "x", missing: ""}
    with pytest.raises(ValueError):
        parse_sale_row(row)


def test_share_of_asking_unknown_without_asking():
    base = {"id": "1", "name": "A", "sold_year": 2025, "sale_price": 2_000_000, "sale_type": "x", "evidence": "y"}
    assert WinerySaleOut(**base, last_asking_price=4_000_000).share_of_asking == 0.5
    assert WinerySaleOut(**base).share_of_asking is None


def test_committed_sales_file_parses():
    import csv
    from scripts._import_common import DATA_DIR

    with open(DATA_DIR / "winery_sales.csv", encoding="utf-8", newline="") as f:
        records = [parse_sale_row(r) for r in csv.DictReader(f)]
    assert records
    assert len({(r["name"], r["sold_year"]) for r in records}) == len(records)
    assert all(r["source_url"] for r in records)
    assert all(len(r["evidence"]) <= 32 and len(r["sale_type"]) <= 32 for r in records)


@pytest.mark.parametrize("text", ["$3,250,000", "Price: 3250000", "CA$3 250 000", "$3.25M", "$3.25 million"])
def test_price_appears_in_common_formats(text):
    assert price_appears(text, 3_250_000)


@pytest.mark.parametrize("text", ["$3,900,000", "13,250,000", "$3,250,0001", ""])
def test_price_doesnt_match_other_numbers(text):
    assert not price_appears(text, 3_250_000)


def test_classify_page():
    assert classify_page(403, "", 100_000) == "blocked"
    assert classify_page(429, "", 100_000) == "blocked"
    assert classify_page(404, "", 100_000) == "page gone"
    assert classify_page(200, "$100,000", 100_000) == "price found"
    assert classify_page(200, "$200,000", 100_000) == "price not found"
    assert classify_page(200, "anything", None) == "loaded, no price to compare"
    assert classify_page(500, "", 100_000) == "error 500"


def test_latest_open_listings_uses_newest_row_and_skips_closed():
    rows = [
        {"advertised_name": "A", "as_of": "2026-10-01", "status": "Advertised"},
        {"advertised_name": "A", "as_of": "2026-11-01", "status": "Sold"},
        {"advertised_name": "B", "as_of": "2026-11-01", "status": "Advertised"},
        {"advertised_name": "B", "as_of": "2026-10-01", "status": "Sold"},
    ]
    assert [r["advertised_name"] for r in latest_open_listings(rows)] == ["B"]
