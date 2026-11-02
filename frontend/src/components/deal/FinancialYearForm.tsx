"use client";

import { useState } from "react";
import { deleteFinancialYear, saveFinancialYear } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Draft, NumberField, toDraft, toNumber } from "@/components/deal/NumberField";
import { ChannelFigures, DealFinancials, FinancialYear, FinancialYearInput, SalesChannel } from "@/types/deal";

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

function yearDraft(year?: FinancialYear): Draft {
  const draft = toDraft(Object.fromEntries(YEAR_FIELDS.map(([key]) => [key, year?.[key]])));
  year?.channels.forEach((c) => {
    CHANNEL_FIELDS.forEach(([field]) => {
      draft[`${c.channel}.${field}`] = c[field] == null ? "" : String(c[field]);
    });
  });
  return draft;
}

interface FinancialYearFormProps {
  data: DealFinancials;
  onSaved: (result: DealFinancials, message: string) => void;
  onFailed: () => void;
  onInvalid: (message: string) => void;
}

export function FinancialYearForm({ data, onSaved, onFailed, onInvalid }: FinancialYearFormProps) {
  const latest = data.years[data.years.length - 1];
  const [selectedYear, setSelectedYear] = useState(latest ? String(latest.fiscal_year) : "");
  const [draft, setDraft] = useState<Draft>(() => yearDraft(latest));

  const pickYear = (value: string) => {
    setSelectedYear(value);
    setDraft(yearDraft(data.years.find((y) => String(y.fiscal_year) === value)));
  };

  const save = (e: React.FormEvent) => {
    e.preventDefault();
    const year = Number(selectedYear);
    if (!Number.isInteger(year) || year < 1980 || year > 2100) {
      onInvalid("Enter a fiscal year between 1980 and 2100.");
      return;
    }
    const channels: ChannelFigures[] = CHANNELS
      .map(([channel]) => ({
        channel,
        cases: toNumber(draft[`${channel}.cases`]),
        revenue: toNumber(draft[`${channel}.revenue`]),
        direct_cost: toNumber(draft[`${channel}.direct_cost`]),
      }))
      .filter((c) => c.cases != null || c.revenue != null || c.direct_cost != null);
    const figures = Object.fromEntries(YEAR_FIELDS.map(([key]) => [key, toNumber(draft[key])]));
    saveFinancialYear(data.deal_id, year, { ...figures, channels })
      .then((result) => onSaved(result, `${year} saved.`))
      .catch(onFailed);
  };

  const remove = () => {
    if (!window.confirm(`Delete the ${selectedYear} figures?`)) return;
    deleteFinancialYear(data.deal_id, Number(selectedYear))
      .then((result) => {
        onSaved(result, `${selectedYear} deleted.`);
        setSelectedYear("");
        setDraft({});
      })
      .catch(onFailed);
  };

  const yearExists = data.years.some((y) => String(y.fiscal_year) === selectedYear);

  return (
    <Card className="p-5">
      <form onSubmit={save} className="space-y-4">
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
          {YEAR_FIELDS.map(([key, label]) => (
            <NumberField key={key} draft={draft} setDraft={setDraft} name={key} label={label} />
          ))}
        </div>
        <h3 className="font-medium text-gray-800">Sales by channel</h3>
        <div className="space-y-3">
          {CHANNELS.map(([channel, label]) => (
            <div key={channel} className="grid gap-3 sm:grid-cols-4 sm:items-end">
              <p className="text-sm font-medium text-gray-700 sm:pb-2">{label}</p>
              {CHANNEL_FIELDS.map(([field, fieldLabel]) => (
                <NumberField key={field} draft={draft} setDraft={setDraft} name={`${channel}.${field}`} label={fieldLabel} />
              ))}
            </div>
          ))}
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="submit">Save year</Button>
          {yearExists && <Button type="button" variant="ghost" onClick={remove}>Delete year</Button>}
        </div>
      </form>
    </Card>
  );
}
