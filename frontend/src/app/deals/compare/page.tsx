"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { compareDeals } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { DealComparison } from "@/types/deal";

const SCENARIO_FIELDS = [
  ["worst_revenue", "Worst: revenue change (%)"],
  ["worst_costs", "Worst: cost change (%)"],
  ["best_revenue", "Best: revenue change (%)"],
  ["best_costs", "Best: cost change (%)"],
] as const;

type ScenarioKey = (typeof SCENARIO_FIELDS)[number][0];

const money = (value?: number | null) => (value == null ? "Unknown" : formatPrice(value, "CAD"));
const multiple = (value?: number | null) => (value == null ? "—" : `${value.toFixed(1)}x`);

export default function CompareDealsPage() {
  const [deals, setDeals] = useState<DealComparison[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [inputs, setInputs] = useState<Record<ScenarioKey, string>>({
    worst_revenue: "-15",
    worst_costs: "10",
    best_revenue: "10",
    best_costs: "-5",
  });

  useEffect(() => {
    const numbers = SCENARIO_FIELDS.map(([key]) => Number(inputs[key]));
    if (SCENARIO_FIELDS.some(([key]) => inputs[key] === "") || numbers.some((n) => n < -100 || n > 100)) return;
    let current = true;
    compareDeals({
      worst_revenue: Number(inputs.worst_revenue),
      worst_costs: Number(inputs.worst_costs),
      best_revenue: Number(inputs.best_revenue),
      best_costs: Number(inputs.best_costs),
    })
      .then((data) => {
        if (current) {
          setDeals(data);
          setError(null);
        }
      })
      .catch(() => {
        if (current) setError("Couldn't load your deals. Check that you're logged in.");
      });
    return () => {
      current = false;
    };
  }, [inputs]);

  const rows: [string, (d: DealComparison) => string][] = [
    ["Stage", (d) => d.stage],
    ["Figures from", (d) => (d.analysis_year ? String(d.analysis_year) : "No figures yet")],
    ["Asking price", (d) => money(d.asking_price)],
    ["Revenue", (d) => money(d.revenue)],
    ["Cases sold", (d) => (d.cases_sold == null ? "Unknown" : d.cases_sold.toLocaleString())],
    ["Property share of price", (d) => (d.property_share == null ? "Unknown" : `${(d.property_share * 100).toFixed(0)}%`)],
    ["Total cash needed", (d) => money(d.total_cash_needed)],
    ...(["Worst", "Expected", "Best"] as const).map((name): [string, (d: DealComparison) => string] => [
      `${name} case earnings (price multiple)`,
      (d) => {
        const scenario = d.scenarios.find((s) => s.name === name);
        return `${money(scenario?.earnings)} (${multiple(scenario?.price_to_earnings)})`;
      },
    ]),
    ["Checks needing review", (d) => String(d.review_count)],
    ["Checks with missing data", (d) => String(d.unknown_count)],
  ];

  return (
    <div className="space-y-6">
      <div>
        <Link href="/deals" className="text-sm text-wine-700 hover:underline inline-flex items-center gap-1 mb-3">
          <ArrowLeft className="h-4 w-4" />
          All deals
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">Compare deals</h1>
        <p className="text-gray-500">Real figures you entered, with your own best and worst cases. Only you can see this.</p>
      </div>

      <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
        The scenario percentages are starting assumptions, not forecasts. Set them with your accountant for each winery. Price multiples use the asking price, not a negotiated one.
      </p>

      {error && (
        <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      <Card className="p-5 space-y-3">
        <h2 className="text-xl font-semibold text-gray-800">Scenarios</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {SCENARIO_FIELDS.map(([key, label]) => (
            <Input
              key={key}
              id={key}
              label={label}
              type="number"
              min={-100}
              max={100}
              value={inputs[key]}
              onChange={(e) => setInputs({ ...inputs, [key]: e.target.value })}
            />
          ))}
        </div>
      </Card>

      {deals && deals.length === 0 && (
        <p className="text-sm text-gray-500">No deals to compare yet. <Link href="/deals" className="underline">Add a deal</Link>.</p>
      )}

      {deals && deals.length > 0 && (
        <Card className="p-5">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-gray-200">
                  <th className="py-2 pr-4 font-medium text-gray-500"><span className="sr-only">Measure</span></th>
                  {deals.map((d) => (
                    <th key={d.deal_id} className="py-2 pr-4 font-semibold min-w-[11rem]">
                      <Link href={`/deals/${d.deal_id}/financials`} className="text-wine-800 hover:underline">{d.name}</Link>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map(([label, value]) => (
                  <tr key={label}>
                    <th scope="row" className="py-2 pr-4 text-left font-medium text-gray-500">{label}</th>
                    {deals.map((d) => <td key={d.deal_id} className="py-2 pr-4 text-gray-800">{value(d)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
