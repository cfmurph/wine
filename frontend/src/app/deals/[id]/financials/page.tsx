"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { deleteFinancialYear, getDealFinancials, saveDealAssumptions, saveFinancialYear } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FinancingModel } from "@/components/deal/FinancingModel";
import { Input } from "@/components/ui/Input";
import { AnalysisCheck, ChannelFigures, CheckLine, DealAssumptions, DealFinancials, FinancialYear, FinancialYearInput, SalesChannel } from "@/types/deal";

const ASSUMPTIONS: [keyof DealAssumptions, string][] = [
  ["asking_price", "Asking price"],
  ["property_value", "Property value (appraised)"],
  ["owner_salary", "Market salary for owner's role"],
  ["working_capital", "Working capital"],
  ["replanting_cost", "Replanting"],
  ["equipment_cost", "Equipment"],
  ["repair_cost", "Deferred repairs"],
  ["inventory_funding", "Inventory funding"],
];

type YearField = Exclude<keyof FinancialYearInput, "channels">;

const YEAR_FIELDS: [YearField, string][] = [
  ["revenue", "Revenue"],
  ["tax_return_revenue", "Revenue on tax return"],
  ["cost_of_goods", "Cost of goods"],
  ["operating_expenses", "Operating expenses"],
  ["owner_addbacks", "Owner add-backs"],
  ["cases_opening", "Opening inventory (cases)"],
  ["cases_produced", "Cases produced"],
  ["cases_sold", "Cases sold"],
  ["cases_closing", "Closing inventory (cases)"],
  ["grape_tonnes", "Grapes crushed (tonnes)"],
];

const CHANNELS: [SalesChannel, string][] = [
  ["tasting_room", "Tasting room"],
  ["wine_club", "Wine club"],
  ["online", "Online"],
  ["restaurants", "Restaurants"],
  ["liquor_stores", "Liquor stores"],
  ["private_retail", "Private retail"],
];

const CHANNEL_FIELDS: ["cases" | "revenue" | "direct_cost", string][] = [
  ["cases", "Cases"],
  ["revenue", "Revenue"],
  ["direct_cost", "Direct cost"],
];

const STATUS: Record<AnalysisCheck["status"], string> = {
  computed: "Calculated",
  review: "Needs review",
  unknown: "Unknown",
};

type Draft = Record<string, string>;

const toDraft = (source: object): Draft =>
  Object.fromEntries(Object.entries(source).map(([k, v]) => [k, v == null ? "" : String(v)]));
const toNumber = (value?: string) => (value ? Number(value) : null);

function emptyYearDraft(year?: FinancialYear): Draft {
  const draft = toDraft(Object.fromEntries(YEAR_FIELDS.map(([key]) => [key, year?.[key]])));
  year?.channels.forEach((c) => {
    CHANNEL_FIELDS.forEach(([field]) => {
      draft[`${c.channel}.${field}`] = c[field] == null ? "" : String(c[field]);
    });
  });
  return draft;
}

function formatLine(line: CheckLine) {
  if (line.value == null) return "Unknown";
  if (line.unit === "currency") return formatPrice(line.value, "CAD");
  if (line.unit === "percent") return `${(line.value * 100).toFixed(1)}%`;
  if (line.unit === "multiple") return `${line.value.toFixed(2)}x`;
  return line.value.toLocaleString(undefined, { maximumFractionDigits: 1 });
}

export default function DealFinancialsPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<DealFinancials | null>(null);
  const [assumptions, setAssumptions] = useState<Draft>({});
  const [selectedYear, setSelectedYear] = useState("");
  const [yearDraft, setYearDraft] = useState<Draft>({});
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);

  useEffect(() => {
    getDealFinancials(id)
      .then((result) => {
        setData(result);
        setAssumptions(toDraft(result.assumptions));
        const latest = result.years[result.years.length - 1];
        if (latest) {
          setSelectedYear(String(latest.fiscal_year));
          setYearDraft(emptyYearDraft(latest));
        }
      })
      .catch(() => setError("Couldn't load this deal. Check that you're logged in."));
  }, [id]);

  const applied = (message: string) => (result: DealFinancials) => {
    setData(result);
    setSaved(message);
    setError(null);
  };
  const failed = () => {
    setSaved(null);
    setError("That wasn't saved. Check for negative or invalid figures and try again.");
  };

  const saveAssumptions = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = Object.fromEntries(ASSUMPTIONS.map(([key]) => [key, toNumber(assumptions[key])])) as DealAssumptions;
    saveDealAssumptions(id, payload).then(applied("Deal figures saved.")).catch(failed);
  };

  const pickYear = (value: string) => {
    setSelectedYear(value);
    setYearDraft(emptyYearDraft(data?.years.find((y) => String(y.fiscal_year) === value)));
  };

  const saveYear = (e: React.FormEvent) => {
    e.preventDefault();
    const year = Number(selectedYear);
    if (!Number.isInteger(year) || year < 1980 || year > 2100) {
      setError("Enter a fiscal year between 1980 and 2100.");
      return;
    }
    const channels: ChannelFigures[] = CHANNELS
      .map(([channel]) => ({
        channel,
        cases: toNumber(yearDraft[`${channel}.cases`]),
        revenue: toNumber(yearDraft[`${channel}.revenue`]),
        direct_cost: toNumber(yearDraft[`${channel}.direct_cost`]),
      }))
      .filter((c) => c.cases != null || c.revenue != null || c.direct_cost != null);
    const figures = Object.fromEntries(YEAR_FIELDS.map(([key]) => [key, toNumber(yearDraft[key])]));
    saveFinancialYear(id, year, { ...figures, channels }).then(applied(`${year} saved.`)).catch(failed);
  };

  const removeYear = () => {
    if (!window.confirm(`Delete the ${selectedYear} figures?`)) return;
    deleteFinancialYear(id, Number(selectedYear))
      .then((result) => {
        applied(`${selectedYear} deleted.`)(result);
        setSelectedYear("");
        setYearDraft({});
      })
      .catch(failed);
  };

  const numberField = (draft: Draft, setDraft: (d: Draft) => void, key: string, label: string) => (
    <Input
      key={key}
      id={`field-${key}`}
      label={label}
      type="number"
      min={0}
      step="any"
      value={draft[key] ?? ""}
      onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
    />
  );

  if (!data) {
    return error ? (
      <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-3">
        <AlertCircle className="h-4 w-4 flex-shrink-0" />
        {error}
      </div>
    ) : (
      <p className="text-gray-400 py-16 text-center">Loading…</p>
    );
  }

  const yearExists = data.years.some((y) => String(y.fiscal_year) === selectedYear);

  return (
    <div className="space-y-6">
      <div>
        <Link href="/deals" className="text-sm text-wine-700 hover:underline inline-flex items-center gap-1 mb-3">
          <ArrowLeft className="h-4 w-4" />
          All deals
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{data.name}: financials</h1>
      </div>

      <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
        Check what your NDA allows before entering a seller&apos;s figures. These checks flag questions for your accountant; they aren&apos;t a valuation.
      </p>

      {error && (
        <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}
      {saved && <p className="text-sm text-green-800 bg-green-50 border border-green-200 rounded-lg px-4 py-3">{saved}</p>}

      <Card className="p-5 space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">
          Screening checks{data.analysis_year ? ` (${data.analysis_year})` : ""}
        </h2>
        <div className="grid gap-4 lg:grid-cols-2">
          {data.checks.map((check) => (
            <div key={check.title} className="border border-gray-100 rounded-lg p-4 space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-medium text-gray-800">{check.title}</h3>
                <Badge variant={check.status === "review" ? "wine" : check.status === "unknown" ? "outline" : "default"}>{STATUS[check.status]}</Badge>
              </div>
              <p className="text-sm text-gray-600">{check.note}</p>
              <dl className="text-sm space-y-1">
                {check.lines.map((line) => (
                  <div key={line.label} className="flex justify-between gap-3">
                    <dt className="text-gray-500">{line.label}</dt>
                    <dd className={line.value == null ? "text-gray-400" : "font-medium text-gray-800"}>{formatLine(line)}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      </Card>

      <FinancingModel dealId={id} refreshKey={data} />

      <Card className="p-5">
        <form onSubmit={saveAssumptions} className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">Deal figures</h2>
          <p className="text-sm text-gray-500">Canadian dollars. Leave blank if unknown; enter 0 only if a cost doesn&apos;t apply.</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {ASSUMPTIONS.map(([key, label]) => numberField(assumptions, setAssumptions, key, label))}
          </div>
          <Button type="submit">Save deal figures</Button>
        </form>
      </Card>

      <Card className="p-5">
        <form onSubmit={saveYear} className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800">Seller&apos;s figures by year</h2>
          <div className="flex flex-wrap items-end gap-3">
            <Input
              id="fiscal-year"
              label="Fiscal year"
              type="number"
              min={1980}
              max={2100}
              value={selectedYear}
              onChange={(e) => pickYear(e.target.value)}
            />
            {data.years.length > 0 && (
              <p className="text-sm text-gray-500 pb-2">Entered: {data.years.map((y) => y.fiscal_year).join(", ")}</p>
            )}
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {YEAR_FIELDS.map(([key, label]) => numberField(yearDraft, setYearDraft, key, label))}
          </div>
          <h3 className="font-medium text-gray-800">Sales by channel</h3>
          <div className="space-y-3">
            {CHANNELS.map(([channel, label]) => (
              <div key={channel} className="grid gap-3 sm:grid-cols-4 sm:items-end">
                <p className="text-sm font-medium text-gray-700 sm:pb-2">{label}</p>
                {CHANNEL_FIELDS.map(([field, fieldLabel]) =>
                  numberField(yearDraft, setYearDraft, `${channel}.${field}`, fieldLabel)
                )}
              </div>
            ))}
          </div>
          <div className="flex flex-wrap gap-3">
            <Button type="submit">Save year</Button>
            {yearExists && <Button type="button" variant="ghost" onClick={removeYear}>Delete year</Button>}
          </div>
        </form>
      </Card>
    </div>
  );
}
