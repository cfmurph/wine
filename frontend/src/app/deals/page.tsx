"use client";

import { useState } from "react";
import Link from "next/link";
import { ClipboardList } from "lucide-react";
import { useFetch } from "@/hooks/useFetch";
import { createDeal, getDeals } from "@/lib/api";
import { DealCard } from "@/components/deal/DealCard";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function DealsPage() {
  const { data: deals, failed: needsLogin, setData: setDeals } = useFetch("deals", getDeals);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");

  const addDeal = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createDeal(name.trim())
      .then((deal) => {
        setDeals((current) => (current?.some((d) => d.id === deal.id) ? current : [...(current ?? []), deal]));
        setName("");
        setError(null);
      })
      .catch(() => setError("That deal wasn't added. Please try again."));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <ClipboardList className="h-8 w-8 text-wine-700" />
          Deal Tracker
        </h1>
        <p className="text-gray-500">
          Track each winery from first contact to offer. Only you can see your deals.{" "}
          {deals && deals.length > 1 && <Link href="/deals/compare" className="underline">Compare deals</Link>}
        </p>
      </div>

      {needsLogin && (
        <p className="text-sm text-gray-600 bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
          <Link href="/profile" className="underline">Log in</Link> to track deals.
        </p>
      )}
      {error && (
        <ErrorMessage>{error}</ErrorMessage>
      )}

      {deals && (
        <>
          <form onSubmit={addDeal} className="flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[16rem]">
              <Input
                id="deal-name"
                label="Add a winery or listing"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <Button type="submit">Add deal</Button>
          </form>

          {deals.length === 0 && (
            <p className="text-gray-500 text-sm">
              No deals yet. Add one above, or use &quot;Track this deal&quot; on a <Link href="/wineries" className="underline">winery page</Link>.
            </p>
          )}

          {deals.map((deal) => (
            <DealCard
              key={deal.id}
              deal={deal}
              onChange={(saved) => setDeals((current) => current?.map((d) => (d.id === saved.id ? saved : d)) ?? null)}
              onRemove={(id) => setDeals((current) => current?.filter((d) => d.id !== id) ?? null)}
              onError={setError}
            />
          ))}
        </>
      )}
    </div>
  );
}
