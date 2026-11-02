"use client";

import { useState } from "react";
import { Input } from "@/components/ui/Input";
import { formatPrice } from "@/lib/utils";

interface AcquisitionEstimateProps {
  statedCases?: number | null;
  bottlePrice?: number | null;
  askingPrice?: number | null;
}

const BOTTLES_PER_CASE = 12;

export function AcquisitionEstimate({ statedCases, bottlePrice, askingPrice }: AcquisitionEstimateProps) {
  const [values, setValues] = useState({
    cases: "",
    bottlePrice: bottlePrice?.toString() ?? "",
    directShare: "",
    wholesaleNet: "",
    costPerCase: "",
    fixedCosts: "",
    askingPrice: askingPrice?.toString() ?? "",
  });

  const field = (key: keyof typeof values, label: string) => (
    <Input
      id={`estimate-${key}`}
      label={label}
      type="number"
      min={0}
      value={values[key]}
      onChange={(e) => setValues({ ...values, [key]: e.target.value })}
    />
  );

  const number = (key: keyof typeof values) => (values[key] === "" ? null : Number(values[key]));
  const caseCount = number("cases");
  const price = number("bottlePrice");
  const directShare = number("directShare");
  const wholesaleNet = number("wholesaleNet");
  const costPerCase = number("costPerCase");
  const fixedCosts = number("fixedCosts");
  const asking = number("askingPrice");

  const revenue =
    caseCount != null && price != null && directShare != null && wholesaleNet != null
      ? caseCount *
        BOTTLES_PER_CASE *
        price *
        (directShare / 100 + (1 - directShare / 100) * (wholesaleNet / 100))
      : null;
  const margin =
    revenue != null && caseCount != null && costPerCase != null && fixedCosts != null
      ? revenue - caseCount * costPerCase - fixedCosts
      : null;

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">
        A what-if calculator. Every input is your own assumption, and only figures found in public
        data are filled in. Results aren&apos;t this winery&apos;s actual financials and exclude
        taxes, debt and capital spending.
        {statedCases != null && ` Public data puts production or capacity at ${statedCases.toLocaleString()} cases, which may not reflect actual sales.`}
      </p>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {field("cases", "Cases sold per year")}
        {field("bottlePrice", "Average retail price per bottle ($)")}
        {field("directShare", "Share sold direct at retail price (%)")}
        {field("wholesaleNet", "Wholesale net as % of retail price")}
        {field("costPerCase", "Cost per case ($)")}
        {field("fixedCosts", "Fixed costs per year ($)")}
        {field("askingPrice", "Purchase price ($)")}
      </div>
      <dl className="grid gap-4 sm:grid-cols-3 text-sm">
        <div>
          <dt className="text-gray-500">Estimated revenue</dt>
          <dd className="text-xl font-semibold">{revenue != null ? formatPrice(revenue, "CAD") : "Needs inputs"}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Estimated operating margin</dt>
          <dd className="text-xl font-semibold">{margin != null ? formatPrice(margin, "CAD") : "Needs inputs"}</dd>
        </div>
        <div>
          <dt className="text-gray-500">Purchase price ÷ revenue</dt>
          <dd className="text-xl font-semibold">
            {revenue && asking != null ? `${(asking / revenue).toFixed(1)}×` : "Needs inputs"}
          </dd>
        </div>
      </dl>
    </div>
  );
}
