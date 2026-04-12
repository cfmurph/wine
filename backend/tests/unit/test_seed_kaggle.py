"""Unit tests for the Kaggle seed script's parsing logic."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.seed_from_kaggle import _extract_vintage, _parse_record, _natural_key


class TestExtractVintage:
    def test_four_digit_year_in_title(self):
        assert _extract_vintage("Nieto Senetiner 2015 Malbec") == 2015

    def test_year_at_end(self):
        assert _extract_vintage("Chateau Margaux 2001") == 2001

    def test_no_year(self):
        assert _extract_vintage("Mystery Wine NV") is None

    def test_ignores_non_wine_years(self):
        # Years outside 1950–2039 should be ignored
        assert _extract_vintage("Wine from 1850") is None
        assert _extract_vintage("Wine from 2045") is None

    def test_picks_first_year(self):
        assert _extract_vintage("2017 Blend released 2019") == 2017


class TestParseRecord:
    def _base(self, **overrides):
        rec = {
            "title": "Nieto Senetiner 2015 Malbec",
            "winery": "Nieto Senetiner",
            "variety": "Malbec",
            "country": "Argentina",
            "province": "Mendoza",
            "region_1": "Luján de Cuyo",
            "region_2": "",
            "designation": "Estate",
            "points": "90",
            "price": "18",
            "description": "A rich, full-bodied Malbec.",
            "taster_name": "Michael Schachner",
        }
        rec.update(overrides)
        return rec

    def test_basic_fields(self):
        result = _parse_record(self._base())
        assert result is not None
        assert result["vintage"] == 2015
        assert result["producer"] == "Nieto Senetiner"
        assert result["country"] == "Argentina"
        assert result["region"] == "Luján de Cuyo"
        assert result["grape_varieties"] == ["Malbec"]
        assert result["_price"] == 18.0
        assert result["_points"] == 90.0
        assert result["source_primary"] == "kaggle_winemag"

    def test_canonical_name_strips_vintage(self):
        result = _parse_record(self._base())
        assert "2015" not in result["canonical_name"]
        assert "Nieto Senetiner" in result["canonical_name"]

    def test_null_price_becomes_none(self):
        result = _parse_record(self._base(price=None))
        assert result["_price"] is None

    def test_null_points_becomes_none(self):
        result = _parse_record(self._base(points=None))
        assert result["_points"] is None

    def test_missing_title_returns_none(self):
        result = _parse_record(self._base(title=""))
        assert result is None

    def test_multi_variety_split(self):
        result = _parse_record(self._base(variety="Cabernet Sauvignon, Merlot, Petit Verdot"))
        assert result["grape_varieties"] == ["Cabernet Sauvignon", "Merlot", "Petit Verdot"]

    def test_falls_back_to_province_for_region(self):
        result = _parse_record(self._base(region_1=""))
        assert result["region"] == "Mendoza"

    def test_appellation_from_designation(self):
        result = _parse_record(self._base(designation="Grand Cru"))
        assert result["appellation"] == "Grand Cru"


class TestNaturalKey:
    def test_key_is_lowercase_name_and_vintage(self):
        record = {"canonical_name": "Château Margaux", "vintage": 2010}
        key = _natural_key(record)
        assert key == "château margaux||2010"

    def test_missing_vintage_uses_zero(self):
        record = {"canonical_name": "Mystery Wine NV", "vintage": None}
        key = _natural_key(record)
        assert key == "mystery wine nv||0"
