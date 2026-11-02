"""Screening checks on a seller's figures. Blank means unknown and never counts as zero.

These checks flag questions for an accountant. They aren't a valuation.
"""

from app.schemas.deal import AnalysisCheck, CheckLine, DealComparisonOut, ScenarioOut

# Judgment calls, shown to the user in each check's note.
CASE_TOLERANCE = 0.05
REVENUE_TOLERANCE = 0.02
CHANNEL_CONCENTRATION = 0.6

_CHANNEL_LABELS = {
    "tasting_room": "Tasting room",
    "wine_club": "Wine club",
    "online": "Online",
    "restaurants": "Restaurants",
    "liquor_stores": "Liquor stores",
    "private_retail": "Private retail",
}


def adjusted_earnings(year, owner_salary):
    """Revenue less costs, adding back owner perks and charging a market salary for running it."""
    figures = (year.revenue, year.cost_of_goods, year.operating_expenses, owner_salary)
    if any(v is None for v in figures):
        return None
    return year.revenue - year.cost_of_goods - year.operating_expenses + (year.owner_addbacks or 0) - owner_salary


def _ratio(top, bottom):
    return top / bottom if top is not None and bottom else None


def _price_check(deal, year):
    earnings = adjusted_earnings(year, deal.owner_salary)
    lines = [
        CheckLine(label="Price / revenue", value=_ratio(deal.asking_price, year.revenue), unit="multiple"),
        CheckLine(label="Adjusted earnings", value=earnings, unit="currency"),
        CheckLine(
            label="Price / adjusted earnings",
            value=_ratio(deal.asking_price, earnings) if earnings and earnings > 0 else None,
            unit="multiple",
        ),
    ]
    if deal.asking_price is None or earnings is None:
        return AnalysisCheck(
            title="Price against earnings", status="unknown", lines=lines,
            note="Needs asking price, revenue, costs and a market owner salary.",
        )
    if earnings <= 0:
        return AnalysisCheck(
            title="Price against earnings", status="review", lines=lines,
            note="Adjusted earnings aren't positive, so the price must rest on property or a turnaround.",
        )
    return AnalysisCheck(
        title="Price against earnings", status="computed", lines=lines,
        note="Compare across your deals. Adjusted earnings charge a market salary and add back owner perks.",
    )


def _property_check(deal):
    business = (
        deal.asking_price - deal.property_value
        if deal.asking_price is not None and deal.property_value is not None else None
    )
    lines = [
        CheckLine(label="Property value", value=deal.property_value, unit="currency"),
        CheckLine(label="Implied business value", value=business, unit="currency"),
        CheckLine(label="Property share of price", value=_ratio(deal.property_value, deal.asking_price), unit="percent"),
    ]
    if business is None:
        return AnalysisCheck(
            title="Property against business", status="unknown", lines=lines,
            note="Needs an asking price and a property value, ideally from a licensed appraiser.",
        )
    if business < 0:
        return AnalysisCheck(
            title="Property against business", status="review", lines=lines,
            note="The property value is above the asking price. Check the value and its source.",
        )
    return AnalysisCheck(
        title="Property against business", status="computed", lines=lines,
        note="The remainder is what you'd pay for the brand and operations.",
    )


def _channel_check(year):
    channels = [c for c in (year.channels or []) if c.get("revenue") is not None]
    total = sum(c["revenue"] for c in channels)
    if not channels or not total:
        return AnalysisCheck(
            title="Margin by channel", status="unknown", lines=[],
            note="Needs revenue by sales channel.",
        )
    lines = []
    largest = max(c["revenue"] for c in channels) / total
    for c in channels:
        label = _CHANNEL_LABELS[c["channel"]]
        lines.append(CheckLine(label=f"{label}: share of sales", value=c["revenue"] / total, unit="percent"))
        margin = (c["revenue"] - c["direct_cost"]) / c["revenue"] if c.get("direct_cost") is not None and c["revenue"] else None
        lines.append(CheckLine(label=f"{label}: margin", value=margin, unit="percent"))
    if largest > CHANNEL_CONCENTRATION:
        return AnalysisCheck(
            title="Margin by channel", status="review", lines=lines,
            note=f"One channel is over {CHANNEL_CONCENTRATION:.0%} of sales (my threshold). Ask what happens if it weakens.",
        )
    return AnalysisCheck(
        title="Margin by channel", status="computed", lines=lines,
        note=f"No channel is over {CHANNEL_CONCENTRATION:.0%} of sales (my threshold).",
    )


def _consistency_check(year):
    expected = (
        year.cases_opening + year.cases_produced - year.cases_sold
        if None not in (year.cases_opening, year.cases_produced, year.cases_sold) else None
    )
    case_gap = year.cases_closing - expected if expected is not None and year.cases_closing is not None else None
    revenue_gap = (
        year.revenue - year.tax_return_revenue
        if year.revenue is not None and year.tax_return_revenue is not None else None
    )
    channel_values = [c["revenue"] for c in (year.channels or []) if c.get("revenue") is not None]
    channel_gap = sum(channel_values) - year.revenue if channel_values and year.revenue is not None else None
    lines = [
        CheckLine(label="Closing cases against expected", value=case_gap, unit="number"),
        CheckLine(label="Revenue against tax return", value=revenue_gap, unit="currency"),
        CheckLine(label="Channel sales against revenue", value=channel_gap, unit="currency"),
        CheckLine(label="Cases made per tonne of grapes", value=_ratio(year.cases_produced, year.grape_tonnes), unit="number"),
    ]
    tolerance_note = f"{CASE_TOLERANCE:.0%} on cases and {REVENUE_TOLERANCE:.0%} on revenue (my thresholds)"
    if case_gap is None and revenue_gap is None and channel_gap is None:
        return AnalysisCheck(
            title="Numbers that should agree", status="unknown", lines=lines,
            note="Needs case counts, tax return revenue or channel sales to compare.",
        )
    base = year.cases_closing or expected or 0
    off = (
        (case_gap is not None and abs(case_gap) > CASE_TOLERANCE * max(base, 1))
        or (revenue_gap is not None and abs(revenue_gap) > REVENUE_TOLERANCE * max(year.revenue, 1))
        or (channel_gap is not None and abs(channel_gap) > REVENUE_TOLERANCE * max(year.revenue, 1))
    )
    if off:
        return AnalysisCheck(
            title="Numbers that should agree", status="review", lines=lines,
            note=f"At least one gap is over {tolerance_note}. Ask the seller to reconcile it.",
        )
    return AnalysisCheck(
        title="Numbers that should agree", status="computed", lines=lines,
        note=f"Figures provided agree within {tolerance_note}.",
    )


def _cash_check(deal):
    parts = [
        ("Asking price", deal.asking_price),
        ("Working capital", deal.working_capital),
        ("Replanting", deal.replanting_cost),
        ("Equipment", deal.equipment_cost),
        ("Deferred repairs", deal.repair_cost),
        ("Inventory funding", deal.inventory_funding),
    ]
    missing = [label for label, value in parts if value is None]
    lines = [CheckLine(label=label, value=value, unit="currency") for label, value in parts]
    total = None if missing else sum(value for _, value in parts)
    lines.append(CheckLine(label="Total cash needed", value=total, unit="currency"))
    if missing:
        return AnalysisCheck(
            title="Cash needed after closing", status="unknown", lines=lines,
            note=f"Still needs: {', '.join(missing).lower()}. Enter 0 where a cost truly doesn't apply.",
        )
    return AnalysisCheck(
        title="Cash needed after closing", status="computed", lines=lines,
        note="Excludes closing costs, taxes and financing, and assumes you pay the asking price.",
    )


def analyze_deal(deal, years):
    """Run the checks on the latest fiscal year. Returns (analysis_year, checks)."""
    latest = max(years, key=lambda y: y.fiscal_year, default=None)
    if latest is None:
        empty = AnalysisCheck(title="Seller figures", status="unknown", note="Add a fiscal year to run the earnings, channel and consistency checks.", lines=[])
        return None, [empty, _property_check(deal), _cash_check(deal)]
    return latest.fiscal_year, [
        _price_check(deal, latest),
        _property_check(deal),
        _channel_check(latest),
        _consistency_check(latest),
        _cash_check(deal),
    ]


def scenario_earnings(year, owner_salary, revenue_change, cost_change):
    """Adjusted earnings with revenue and all costs moved by the given fractions, e.g. -0.15."""
    earnings = adjusted_earnings(year, owner_salary)
    if earnings is None:
        return None
    return earnings + year.revenue * revenue_change - (year.cost_of_goods + year.operating_expenses) * cost_change


def compare_deal(deal, years, worst, best):
    """One comparison row. worst and best are (revenue_change, cost_change) fractions."""
    analysis_year, checks = analyze_deal(deal, years)
    latest = max(years, key=lambda y: y.fiscal_year, default=None)
    cash = _cash_check(deal).lines[-1].value
    scenarios = []
    for name, (revenue_change, cost_change) in (("Worst", worst), ("Expected", (0.0, 0.0)), ("Best", best)):
        earnings = scenario_earnings(latest, deal.owner_salary, revenue_change, cost_change) if latest else None
        scenarios.append(ScenarioOut(
            name=name,
            revenue_change=revenue_change,
            cost_change=cost_change,
            earnings=earnings,
            price_to_earnings=_ratio(deal.asking_price, earnings) if earnings and earnings > 0 else None,
        ))
    return DealComparisonOut(
        deal_id=deal.id,
        name=deal.name,
        stage=deal.stage,
        analysis_year=analysis_year,
        asking_price=deal.asking_price,
        revenue=latest.revenue if latest else None,
        cases_sold=latest.cases_sold if latest else None,
        property_share=_ratio(deal.property_value, deal.asking_price),
        total_cash_needed=cash,
        review_count=sum(c.status == "review" for c in checks),
        unknown_count=sum(c.status == "unknown" for c in checks),
        scenarios=scenarios,
    )
