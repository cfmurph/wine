"use client";

import { useState } from "react";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { addDealItem, deleteDeal, deleteDealItem, updateDeal, updateDealItem } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Deal, DealItem, DealItemKind, DealStage, DealUpdate } from "@/types/deal";

const STAGES: [DealStage, string][] = [
  ["researching", "Researching"],
  ["contacted", "Contacted"],
  ["nda", "NDA"],
  ["financials", "Financials received"],
  ["offer", "Offer"],
  ["closed", "Closed"],
  ["passed", "Passed"],
];

const SECTIONS: [DealItemKind, string][] = [
  ["document", "Documents to request"],
  ["advisor", "Advisor checks"],
];

interface DealCardProps {
  deal: Deal;
  onChange: (deal: Deal) => void;
  onRemove: (id: string) => void;
  onError: (message: string) => void;
}

export function DealCard({ deal, onChange, onRemove, onError }: DealCardProps) {
  const [newItems, setNewItems] = useState<Partial<Record<DealItemKind, string>>>({});
  const failed = () => onError("That change wasn't saved. Please try again.");

  const save = (payload: DealUpdate) => updateDeal(deal.id, payload).then(onChange).catch(failed);
  const setItem = (item: DealItem, payload: { done?: boolean; assignee?: string | null }) =>
    updateDealItem(deal.id, item.id, payload)
      .then((saved) => onChange({ ...deal, items: deal.items.map((i) => (i.id === item.id ? saved : i)) }))
      .catch(failed);
  const removeItem = (item: DealItem) =>
    deleteDealItem(deal.id, item.id)
      .then(() => onChange({ ...deal, items: deal.items.filter((i) => i.id !== item.id) }))
      .catch(failed);
  const addItem = (kind: DealItemKind) => {
    const title = newItems[kind]?.trim();
    if (!title) return;
    addDealItem(deal.id, kind, title)
      .then((saved) => {
        onChange({ ...deal, items: [...deal.items, saved] });
        setNewItems({ ...newItems, [kind]: "" });
      })
      .catch(failed);
  };
  const remove = () => {
    if (window.confirm(`Delete the deal for ${deal.name}, including its notes and checklist?`)) {
      deleteDeal(deal.id).then(() => onRemove(deal.id)).catch(failed);
    }
  };

  const doneCount = deal.items.filter((i) => i.done).length;

  return (
    <Card className="p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-gray-800">
            {deal.winery_id ? (
              <Link href={`/wineries/${deal.winery_id}`} className="text-wine-800 hover:underline">{deal.name}</Link>
            ) : (
              deal.name
            )}
          </h2>
          <p className="text-sm text-gray-500">
            {doneCount} of {deal.items.length} checklist items done ·{" "}
            <Link href={`/deals/${deal.id}/financials`} className="underline">Financials</Link>
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={remove} aria-label={`Delete deal for ${deal.name}`}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="space-y-1">
          <label htmlFor={`stage-${deal.id}`} className="block text-sm font-medium text-gray-700">Stage</label>
          <select
            id={`stage-${deal.id}`}
            value={deal.stage}
            onChange={(e) => save({ stage: e.target.value as DealStage })}
            className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm"
          >
            {STAGES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </div>
        <Input
          id={`next-${deal.id}`}
          label="Next step"
          defaultValue={deal.next_step ?? ""}
          onBlur={(e) => e.target.value !== (deal.next_step ?? "") && save({ next_step: e.target.value || null })}
        />
        <Input
          id={`due-${deal.id}`}
          label="Due"
          type="date"
          value={deal.next_step_due ?? ""}
          onChange={(e) => save({ next_step_due: e.target.value || null })}
        />
      </div>

      <div className="space-y-1">
        <label htmlFor={`notes-${deal.id}`} className="block text-sm font-medium text-gray-700">Notes</label>
        <textarea
          id={`notes-${deal.id}`}
          rows={2}
          defaultValue={deal.notes ?? ""}
          onBlur={(e) => e.target.value !== (deal.notes ?? "") && save({ notes: e.target.value || null })}
          className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {SECTIONS.map(([kind, label]) => (
          <div key={kind} className="space-y-2">
            <h3 className="font-medium text-gray-800">{label}</h3>
            <ul className="space-y-2">
              {deal.items.filter((i) => i.kind === kind).map((item) => (
                <li key={item.id} className="text-sm">
                  <div className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      checked={item.done}
                      onChange={(e) => setItem(item, { done: e.target.checked })}
                      aria-label={item.title}
                      className="mt-0.5 accent-wine-700"
                    />
                    <span className={item.done ? "flex-1 text-gray-400 line-through" : "flex-1 text-gray-700"}>{item.title}</span>
                    <button type="button" onClick={() => removeItem(item)} aria-label={`Remove ${item.title}`} className="text-gray-400 hover:text-red-600">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                  <input
                    defaultValue={item.assignee ?? ""}
                    placeholder="Who has this?"
                    aria-label={`Who has ${item.title}`}
                    onBlur={(e) => e.target.value !== (item.assignee ?? "") && setItem(item, { assignee: e.target.value || null })}
                    className="ml-6 mt-1 w-[calc(100%-1.5rem)] border-b border-gray-200 text-xs text-gray-600 placeholder:text-gray-400 focus:outline-none focus:border-wine-500"
                  />
                </li>
              ))}
            </ul>
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                addItem(kind);
              }}
            >
              <Input
                aria-label={`Add to ${label}`}
                placeholder="Add an item"
                value={newItems[kind] ?? ""}
                onChange={(e) => setNewItems({ ...newItems, [kind]: e.target.value })}
              />
              <Button type="submit" variant="secondary" size="sm">Add</Button>
            </form>
          </div>
        ))}
      </div>
    </Card>
  );
}
