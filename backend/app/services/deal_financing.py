"""Loan payments and debt coverage for a deal. Rates and terms come from the user, never defaults.

Payments use semi-annual compounding, the usual convention for fixed-rate Canadian mortgages. A lender's
actual terms may differ.
"""

from app.schemas.deal import FinancingIn, FinancingOut
from app.services.deal_analysis import adjusted_earnings

_MONTHS_PER_YEAR = 12


def _monthly_rate(annual_rate: float) -> float:
    return (1 + annual_rate / 2) ** (1 / 6) - 1


def monthly_payment(loan: float, annual_rate: float, years: int) -> float:
    months = years * _MONTHS_PER_YEAR
    if annual_rate == 0:
        return loan / months
    rate = _monthly_rate(annual_rate)
    return loan * rate / (1 - (1 + rate) ** -months)


def loan_for_payment(payment: float, annual_rate: float, years: int) -> float:
    """The largest loan a monthly payment can carry."""
    months = years * _MONTHS_PER_YEAR
    if annual_rate == 0:
        return payment * months
    rate = _monthly_rate(annual_rate)
    return payment * (1 - (1 + rate) ** -months) / rate


def model_financing(deal, years, inputs: FinancingIn) -> FinancingOut:
    price = inputs.purchase_price if inputs.purchase_price is not None else deal.asking_price
    latest = max(years, key=lambda y: y.fiscal_year, default=None)
    earnings = adjusted_earnings(latest, deal.owner_salary) if latest else None
    rate = inputs.annual_rate_percent / 100
    share_down = inputs.down_payment_percent / 100

    other_costs = [
        ("working capital", deal.working_capital),
        ("replanting", deal.replanting_cost),
        ("equipment", deal.equipment_cost),
        ("deferred repairs", deal.repair_cost),
        ("inventory funding", deal.inventory_funding),
    ]
    missing = [label for label, value in other_costs if value is None]
    other_total = sum(value for _, value in other_costs if value is not None)

    down = loan = payment = annual = coverage = stressed = cash_needed = shortfall = None
    if price is not None:
        down = price * share_down
        loan = price - down
        payment = monthly_payment(loan, rate, inputs.amortization_years)
        annual = payment * _MONTHS_PER_YEAR
        stressed_annual = monthly_payment(loan, rate + inputs.rate_stress_points / 100, inputs.amortization_years) * _MONTHS_PER_YEAR
        if earnings is not None and annual:
            coverage = earnings / annual
            stressed = earnings / stressed_annual
        if not missing:
            cash_needed = down + other_total
            if inputs.available_cash is not None:
                shortfall = max(cash_needed - inputs.available_cash, 0)

    max_loan = None
    if earnings is not None:
        capacity = max(earnings, 0) / inputs.min_coverage / _MONTHS_PER_YEAR
        max_loan = loan_for_payment(capacity, rate, inputs.amortization_years)

    max_price = None
    if inputs.available_cash is not None and not missing:
        cash_for_down = max(inputs.available_cash - other_total, 0)
        limits = []
        if share_down > 0:
            limits.append(cash_for_down / share_down)
        if max_loan is not None:
            limits.append(cash_for_down + max_loan)
        max_price = min(limits) if limits else None

    return FinancingOut(
        purchase_price=price,
        down_payment=down,
        loan=loan,
        monthly_payment=payment,
        annual_debt_service=annual,
        adjusted_earnings=earnings,
        analysis_year=latest.fiscal_year if latest else None,
        coverage=coverage,
        stressed_coverage=stressed,
        max_loan_from_earnings=max_loan,
        other_cash_costs=other_total,
        missing_cash_costs=missing,
        cash_needed=cash_needed,
        cash_shortfall=shortfall,
        max_price_for_cash=max_price,
    )
