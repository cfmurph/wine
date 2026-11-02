"use client";

import { useState } from "react";
import { modelFinancing } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { DealFinancials, FinancingResult } from "@/types/deal";

const FIELDS = [
  ["purchase_price", "Purchase price (blank uses asking)", false],
  ["down_payment_percent", "Down payment (%)", true],
  ["annual_rate_percent", "Interest rate (%)", true],
  ["amortization_years", "Amortization (years)", true],
  ["available_cash", "Cash you have available", false],
  ["min_coverage", "Lender's minimum coverage", true],
  ["rate_stress_points", "Rate stress test (added points)", true],
] as const;

type FieldKey = (typeof FIELDS)[number][0];

const money = (value?: number | null) => (value == null ? "Unknown" : formatPrice(Math.round(value), "CAD"));
const ratio = (value?: number | null) => (value == null ? "Unknown" : `${value.toFixed(2)}x`);

export function FinancingModel({ dealId, refreshKey }: { dealId: string; refreshKey: DealFinancials }) {
  const [inputs, setInputs] = useState<Record<FieldKey, string>>({
    purchase_price: "",
    down_payment_percent: "",
    annual_rate_percent: "",
    amortization_years: "",
    available_cash: "",
    min_coverage: "1.25",
    rate_stress_points: "2",
  });
  const [result, setResult] = useState<{ value: FinancingResult; basedOn: DealFinancials } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const calculate = (e: React.FormEvent) => {
    e.preventDefault();
    modelFinancing(dealId, {
      purchase_price: inputs.purchase_price ? Number(inputs.purchase_price) : null,
      down_payment_percent: Number(inputs.down_payment_percent),
      annual_rate_percent: Number(inputs.annual_rate_percent),
      amortization_years: Number(inputs.amortization_years),
      available_cash: inputs.available_cash ? Number(inputs.available_cash) : null,
      min_coverage: Number(inputs.min_coverage),
      rate_stress_points: Number(inputs.rate_stress_points),
    })
      .then((value) => {
        setResult({ value, basedOn: refreshKey });
        setError(null);
      })
      .catch(() => setError("Couldn't calculate. Check that each figure is in a sensible range."));
  };

  const value = result?.basedOn === refreshKey ? result.value : null;
  const rows: [string, string][] = value
    ? [
        ["Purchase price", money(value.purchase_price)],
        ["Down payment", money(value.down_payment)],
        ["Loan", money(value.loan)],
        ["Monthly payment", money(value.monthly_payment)],
        ["Annual debt payments", money(value.annual_debt_service)],
        [`Adjusted earnings${value.analysis_year ? ` (${value.analysis_year})` : ""}`, money(value.adjusted_earnings)],
        ["Debt coverage", ratio(value.coverage)],
        ["Debt coverage with stressed rate", ratio(value.stressed_coverage)],
        ["Largest loan earnings support", money(value.max_loan_from_earnings)],
        ["Cash needed at and after closing", money(value.cash_needed)],
        ["Cash shortfall", money(value.cash_shortfall)],
        ["Highest price your cash and earnings support", money(value.max_price_for_cash)],
      ]
    : [];

  return (
    <Card className="p-5">
      <form onSubmit={calculate} className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Financing model</h2>
        <p className="text-sm text-gray-500">
          Use a lender&apos;s actual quote. Payments assume semi-annual compounding, common for fixed Canadian mortgages. Coverage of 1.25x and a 2-point stress are starting assumptions, so confirm them with your lender. Nothing here is saved.
        </p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {FIELDS.map(([key, label, required]) => (
            <Input
              key={key}
              id={`financing-${key}`}
              label={label}
              type="number"
              min={0}
              step="any"
              required={required}
              value={inputs[key]}
              onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
            />
          ))}
        </div>
        <Button type="submit">Calculate</Button>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {value && (
          <>
            <dl className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
              {rows.map(([label, display]) => (
                <div key={label} className="flex justify-between gap-3 border-b border-gray-100 py-1">
                  <dt className="text-gray-500">{label}</dt>
                  <dd className={display === "Unknown" ? "text-gray-400" : "font-medium text-gray-800"}>{display}</dd>
                </div>
              ))}
            </dl>
            {value.missing_cash_costs.length > 0 && (
              <p className="text-sm text-gray-500">
                Cash totals are unknown until these deal figures are entered: {value.missing_cash_costs.join(", ")}.
              </p>
            )}
          </>
        )}
      </form>
    </Card>
  );
}
