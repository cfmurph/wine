"""Unit tests for the financing model (no DB required)."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.deal import FinancingIn
from app.services.deal_financing import loan_for_payment, model_financing, monthly_payment


def _deal(**overrides):
    values = dict.fromkeys((
        "asking_price", "owner_salary", "working_capital", "replanting_cost",
        "equipment_cost", "repair_cost", "inventory_funding",
    ))
    return SimpleNamespace(**{**values, **overrides})


def _year(fiscal_year=2025, revenue=1_000_000, cost_of_goods=400_000, operating_expenses=300_000, owner_addbacks=None):
    return SimpleNamespace(
        fiscal_year=fiscal_year, revenue=revenue, cost_of_goods=cost_of_goods,
        operating_expenses=operating_expenses, owner_addbacks=owner_addbacks,
    )


def _inputs(**overrides):
    return FinancingIn(**{"down_payment_percent": 30, "annual_rate_percent": 6, "amortization_years": 25, **overrides})


FULL_COSTS = dict(working_capital=100_000, replanting_cost=0, equipment_cost=50_000, repair_cost=0, inventory_funding=0)


def test_payment_matches_canadian_semi_annual_compounding():
    # $100,000 at 6% over 25 years with semi-annual compounding.
    assert monthly_payment(100_000, 0.06, 25) == pytest.approx(639.81, abs=0.01)


def test_zero_rate_divides_evenly():
    assert monthly_payment(120_000, 0, 10) == 1000


def test_loan_for_payment_inverts_payment():
    assert loan_for_payment(monthly_payment(500_000, 0.07, 20), 0.07, 20) == pytest.approx(500_000)
    assert loan_for_payment(1000, 0, 10) == 120_000


def test_uses_asking_price_unless_overridden():
    assert model_financing(_deal(asking_price=1_000_000), [], _inputs()).loan == 700_000
    assert model_financing(_deal(asking_price=1_000_000), [], _inputs(purchase_price=500_000)).loan == 350_000


def test_no_price_leaves_loan_unknown():
    result = model_financing(_deal(), [], _inputs())
    assert result.loan is None
    assert result.monthly_payment is None


def test_coverage_needs_earnings_and_falls_under_rate_stress():
    deal = _deal(asking_price=1_000_000, owner_salary=100_000)
    result = model_financing(deal, [_year()], _inputs())
    assert result.adjusted_earnings == 200_000
    assert result.coverage == pytest.approx(200_000 / result.annual_debt_service)
    assert result.stressed_coverage < result.coverage
    assert model_financing(_deal(asking_price=1_000_000), [], _inputs()).coverage is None


def test_uses_latest_year():
    deal = _deal(asking_price=1_000_000, owner_salary=0)
    result = model_financing(deal, [_year(2025), _year(2023, revenue=9_000_000)], _inputs())
    assert result.analysis_year == 2025


def test_max_loan_is_zero_when_earnings_are_negative():
    deal = _deal(asking_price=1_000_000, owner_salary=500_000)
    assert model_financing(deal, [_year()], _inputs()).max_loan_from_earnings == 0


def test_max_loan_meets_required_coverage():
    deal = _deal(asking_price=1_000_000, owner_salary=100_000)
    result = model_financing(deal, [_year()], _inputs(min_coverage=1.25))
    annual = monthly_payment(result.max_loan_from_earnings, 0.06, 25) * 12
    assert 200_000 / annual == pytest.approx(1.25)


def test_cash_stays_unknown_while_costs_are_missing():
    result = model_financing(_deal(asking_price=1_000_000), [], _inputs(available_cash=500_000))
    assert result.cash_needed is None
    assert result.cash_shortfall is None
    assert result.max_price_for_cash is None
    assert "working capital" in result.missing_cash_costs


def test_cash_shortfall():
    deal = _deal(asking_price=1_000_000, **FULL_COSTS)
    assert model_financing(deal, [], _inputs(available_cash=400_000)).cash_needed == 450_000
    assert model_financing(deal, [], _inputs(available_cash=400_000)).cash_shortfall == 50_000
    assert model_financing(deal, [], _inputs(available_cash=900_000)).cash_shortfall == 0


def test_max_price_takes_the_tighter_limit():
    deal = _deal(asking_price=1_000_000, owner_salary=100_000, **FULL_COSTS)
    result = model_financing(deal, [_year()], _inputs(available_cash=450_000))
    by_down_payment = 300_000 / 0.3
    by_earnings = 300_000 + result.max_loan_from_earnings
    assert result.max_price_for_cash == pytest.approx(min(by_down_payment, by_earnings))


def test_cash_short_of_other_costs_supports_no_down_payment():
    deal = _deal(asking_price=1_000_000, **FULL_COSTS)
    assert model_financing(deal, [], _inputs(available_cash=100_000)).max_price_for_cash == 0


def test_rejects_out_of_range_inputs():
    for bad in ({"down_payment_percent": 101}, {"annual_rate_percent": -1}, {"amortization_years": 0}, {"min_coverage": 0.5}):
        with pytest.raises(ValidationError):
            _inputs(**bad)


def test_rate_and_term_have_no_defaults():
    with pytest.raises(ValidationError):
        FinancingIn(down_payment_percent=30)
