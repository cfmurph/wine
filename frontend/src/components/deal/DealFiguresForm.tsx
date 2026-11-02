"use client";

import { useState } from "react";
import { saveDealAssumptions } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Draft, NumberField, toDraft, toNumber } from "@/components/deal/NumberField";
import { DealAssumptions, DealFinancials } from "@/types/deal";

const FIELDS: [keyof DealAssumptions, string][] = [
  ["asking_price", "Asking price"],
  ["property_value", "Property value (appraised)"],
  ["owner_salary", "Market salary for owner's role"],
  ["working_capital", "Working capital"],
  ["replanting_cost", "Replanting"],
  ["equipment_cost", "Equipment"],
  ["repair_cost", "Deferred repairs"],
  ["inventory_funding", "Inventory funding"],
];

interface DealFiguresFormProps {
  data: DealFinancials;
  onSaved: (result: DealFinancials, message: string) => void;
  onFailed: () => void;
}

export function DealFiguresForm({ data, onSaved, onFailed }: DealFiguresFormProps) {
  const [draft, setDraft] = useState<Draft>(() => toDraft(data.assumptions));

  const save = (e: React.FormEvent) => {
    e.preventDefault();
    const payload = Object.fromEntries(FIELDS.map(([key]) => [key, toNumber(draft[key])])) as DealAssumptions;
    saveDealAssumptions(data.deal_id, payload)
      .then((result) => onSaved(result, "Deal figures saved."))
      .catch(onFailed);
  };

  return (
    <Card className="p-5">
      <form onSubmit={save} className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Deal figures</h2>
        <p className="text-sm text-gray-500">Canadian dollars. Leave blank if unknown; enter 0 only if a cost doesn&apos;t apply.</p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {FIELDS.map(([key, label]) => (
            <NumberField key={key} draft={draft} setDraft={setDraft} name={key} label={label} />
          ))}
        </div>
        <Button type="submit">Save deal figures</Button>
      </form>
    </Card>
  );
}
