"""Unit tests for deal screening checks (no DB required)."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.deal import DealAssumptions, FinancialYearIn
from app.services.deal_analysis import adjusted_earnings, analyze_deal, compare_deal, scenario_earnings


def _deal(**overrides):
    values = dict.fromkeys((
        "asking_price", "property_value", "owner_salary", "working_capital",
        "replanting_cost", "equipment_cost", "repair_cost", "inventory_funding",
    ))
    return SimpleNamespace(**{**values, **overrides})


def _year(fiscal_year=2025, **overrides):
    values = dict.fromkeys((
        "revenue", "tax_return_revenue", "cost_of_goods", "operating_expenses", "owner_addbacks",
        "cases_opening", "cases_produced", "cases_sold", "cases_closing", "grape_tonnes",
    ))
    return SimpleNamespace(fiscal_year=fiscal_year, channels=[], **{**values, **overrides})


def _check(checks, title):
    return next(c for c in checks if c.title == title)


def _line(check, label):
    return next(l for l in check.lines if l.label == label).value


def test_adjusted_earnings_adds_back_perks_and_charges_salary():
    year = _year(revenue=1000, cost_of_goods=300, operating_expenses=400, owner_addbacks=50)
    assert adjusted_earnings(year, 100) == 250


def test_blank_addbacks_count_as_none_given_but_blank_costs_stay_unknown():
    assert adjusted_earnings(_year(revenue=1000, cost_of_goods=300, operating_expenses=400), 100) == 200
    assert adjusted_earnings(_year(revenue=1000, cost_of_goods=None, operating_expenses=400), 100) is None
    assert adjusted_earnings(_year(revenue=1000, cost_of_goods=300, operating_expenses=400), None) is None


def test_no_years_leaves_earnings_checks_unknown():
    year, checks = analyze_deal(_deal(), [])
    assert year is None
    assert all(c.status == "unknown" for c in checks)


def test_uses_latest_year_regardless_of_order():
    year, _ = analyze_deal(_deal(), [_year(2025), _year(2023), _year(2024)])
    assert year == 2025


def test_price_multiple_computed():
    deal = _deal(asking_price=3_000_000, owner_salary=100_000)
    year = _year(revenue=1_000_000, cost_of_goods=400_000, operating_expenses=300_000)
    check = _check(analyze_deal(deal, [year])[1], "Price against earnings")
    assert check.status == "computed"
    assert _line(check, "Price / revenue") == 3
    assert _line(check, "Price / adjusted earnings") == 15


def test_losses_are_flagged_without_a_multiple():
    deal = _deal(asking_price=3_000_000, owner_salary=100_000)
    year = _year(revenue=500_000, cost_of_goods=400_000, operating_expenses=300_000)
    check = _check(analyze_deal(deal, [year])[1], "Price against earnings")
    assert check.status == "review"
    assert _line(check, "Price / adjusted earnings") is None


def test_property_above_price_needs_review():
    check = _check(analyze_deal(_deal(asking_price=2, property_value=3), [])[1], "Property against business")
    assert check.status == "review"


def test_property_share_and_implied_business():
    check = _check(analyze_deal(_deal(asking_price=4_000_000, property_value=3_000_000), [])[1], "Property against business")
    assert check.status == "computed"
    assert _line(check, "Implied business value") == 1_000_000
    assert _line(check, "Property share of price") == 0.75


def test_channel_concentration_flagged():
    year = _year()
    year.channels = [
        {"channel": "tasting_room", "revenue": 700, "direct_cost": 200},
        {"channel": "wine_club", "revenue": 300, "direct_cost": None},
    ]
    check = _check(analyze_deal(_deal(), [year])[1], "Margin by channel")
    assert check.status == "review"
    assert _line(check, "Tasting room: margin") == pytest.approx(500 / 700)
    assert _line(check, "Wine club: margin") is None


def test_balanced_channels_computed():
    year = _year()
    year.channels = [{"channel": "online", "revenue": 500}, {"channel": "restaurants", "revenue": 500}]
    assert _check(analyze_deal(_deal(), [year])[1], "Margin by channel").status == "computed"


def test_case_gap_flagged_and_tolerance_respected():
    bad = _year(cases_opening=1000, cases_produced=5000, cases_sold=4000, cases_closing=1000)
    fine = _year(cases_opening=1000, cases_produced=5000, cases_sold=4000, cases_closing=1950)
    assert _check(analyze_deal(_deal(), [bad])[1], "Numbers that should agree").status == "review"
    assert _check(analyze_deal(_deal(), [fine])[1], "Numbers that should agree").status == "computed"


def test_revenue_mismatch_with_tax_return_flagged():
    year = _year(revenue=1_000_000, tax_return_revenue=800_000)
    check = _check(analyze_deal(_deal(), [year])[1], "Numbers that should agree")
    assert check.status == "review"
    assert _line(check, "Revenue against tax return") == 200_000


def test_nothing_to_compare_is_unknown():
    assert _check(analyze_deal(_deal(), [_year()])[1], "Numbers that should agree").status == "unknown"


def test_cash_total_needs_every_part_but_zero_counts():
    full = _deal(asking_price=100, working_capital=10, replanting_cost=0, equipment_cost=0, repair_cost=5, inventory_funding=0)
    check = _check(analyze_deal(full, [])[1], "Cash needed after closing")
    assert check.status == "computed"
    assert _line(check, "Total cash needed") == 115
    partial = _check(analyze_deal(_deal(asking_price=100), [])[1], "Cash needed after closing")
    assert partial.status == "unknown"
    assert _line(partial, "Total cash needed") is None


def test_rejects_negative_figures_and_unknown_channels():
    with pytest.raises(ValidationError):
        DealAssumptions(asking_price=-1)
    with pytest.raises(ValidationError):
        FinancialYearIn(revenue=-1)
    with pytest.raises(ValidationError):
        FinancialYearIn(channels=[{"channel": "other"}])


def test_scenario_moves_revenue_and_costs():
    year = _year(revenue=1000, cost_of_goods=300, operating_expenses=400)
    assert scenario_earnings(year, 100, 0, 0) == 200
    assert scenario_earnings(year, 100, -0.1, 0.1) == pytest.approx(30)


def test_scenario_stays_unknown_without_figures():
    assert scenario_earnings(_year(revenue=1000), 100, -0.1, 0.1) is None


def test_compare_row_with_figures():
    deal = _deal(name="A", id="1", stage="nda", asking_price=2000, property_value=1000, owner_salary=100)
    year = _year(revenue=1000, cost_of_goods=300, operating_expenses=400, cases_sold=50)
    row = compare_deal(deal, [year], (-0.5, 0.0), (0.1, 0.0))
    assert row.property_share == 0.5
    assert row.cases_sold == 50
    assert [s.name for s in row.scenarios] == ["Worst", "Expected", "Best"]
    assert row.scenarios[1].earnings == 200
    assert row.scenarios[1].price_to_earnings == 10
    assert row.scenarios[0].earnings == -300
    assert row.scenarios[0].price_to_earnings is None
    assert row.scenarios[2].earnings == 300


def test_compare_row_without_figures_is_unknown_not_zero():
    row = compare_deal(_deal(name="B", id="2", stage="researching"), [], (-0.1, 0.1), (0.1, -0.1))
    assert row.revenue is None
    assert row.total_cash_needed is None
    assert row.analysis_year is None
    assert all(s.earnings is None for s in row.scenarios)
    assert row.unknown_count == 3
