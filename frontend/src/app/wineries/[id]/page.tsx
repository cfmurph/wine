"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { useFetch } from "@/hooks/useFetch";
import { createDeal, getWinery } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { AcquisitionEstimate } from "@/components/winery/AcquisitionEstimate";
import { LandRiskCard } from "@/components/winery/LandRiskCard";
import { dataCoverage, formatWineryScore, ScoreBreakdown, ScreeningNotice } from "@/components/winery/ScoreBreakdown";
import { WeightControls } from "@/components/winery/WeightControls";
import { DEFAULT_WEIGHTS, WineryListing } from "@/types/winery";

function stated(value?: boolean | null) {
  return value == null ? "Not stated" : value ? "Yes" : "No";
}

function ListingCard({ listing }: { listing: WineryListing }) {
  const facts: [string, string][] = [
    ["Asking price", listing.asking_price != null ? formatPrice(listing.asking_price, listing.currency) : "Not stated"],
    ["Previous asking", listing.previous_asking_price != null ? formatPrice(listing.previous_asking_price, listing.currency) : "—"],
    ["Total acres", listing.total_acres?.toString() ?? "Not stated"],
    ["Planted acres", listing.planted_acres?.toString() ?? "Not stated"],
    ["Stated capacity (cases)", listing.capacity_cases?.toLocaleString() ?? "Not stated"],
    ["Licence included", stated(listing.includes_licence)],
    ["Brand included", stated(listing.includes_brand)],
    ["Inventory included", stated(listing.includes_inventory)],
    ["Equipment included", stated(listing.includes_equipment)],
  ];
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-semibold text-gray-800">{listing.advertised_name}</h3>
        {listing.status && <Badge variant="wine">{listing.status}</Badge>}
      </div>
      <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2 lg:grid-cols-3 text-sm">
        {facts.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-3 border-b border-gray-100 pb-1">
            <dt className="text-gray-500">{label}</dt>
            <dd className="font-medium text-gray-800 text-right">{value}</dd>
          </div>
        ))}
      </dl>
      {listing.notes && <p className="text-sm text-gray-600">{listing.notes}</p>}
      <p className="text-xs text-gray-500">
        Asking prices, not sale prices. As of {listing.as_of ?? "unknown date"}.{" "}
        {listing.source_url && <a href={listing.source_url} target="_blank" rel="noreferrer" className="underline">Source</a>}
        {" "}Confirm with the listing agent.
      </p>
    </div>
  );
}

export default function WineryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const { data: winery, failed } = useFetch(`${id}:${JSON.stringify(weights)}`, () => getWinery(id, weights));
  const [tracking, setTracking] = useState<string | null>(null);

  const trackDeal = () =>
    createDeal(winery!.name, winery!.id)
      .then(() => setTracking("Added to your deals."))
      .catch(() => setTracking("Log in to track this deal."));

  if (failed) return <ErrorMessage>Couldn&apos;t load this winery.</ErrorMessage>;
  if (!winery) return <p className="text-gray-400 py-16 text-center">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <Link href="/wineries" className="text-sm text-wine-700 hover:underline inline-flex items-center gap-1 mb-3">
          <ArrowLeft className="h-4 w-4" />
          All wineries
        </Link>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-3xl font-bold text-gray-900">{winery.name}</h1>
          <div className="flex items-center gap-3">
            {tracking && <span className="text-sm text-gray-600">{tracking}</span>}
            <Button variant="secondary" size="sm" onClick={trackDeal}>Track this deal</Button>
          </div>
        </div>
        <p className="text-gray-500">
          {[winery.street, winery.city, winery.region].filter(Boolean).join(", ")}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Licence {winery.licence_number}
          {winery.licensee && ` · ${winery.licensee}`}
          {winery.licence_expiry && ` · expires ${winery.licence_expiry}`}
        </p>
      </div>

      <ScreeningNotice />

      {winery.listings.length > 0 && (
        <Card className="p-5 space-y-6">
          <h2 className="text-xl font-semibold text-gray-800">Sale listing</h2>
          {winery.listings.map((listing) => <ListingCard key={listing.id} listing={listing} />)}
        </Card>
      )}

      <Card className="p-5 space-y-5">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="text-xl font-semibold text-gray-800">Screening score</h2>
          <span className="text-sm text-gray-500">
            <strong className="text-2xl text-gray-900">{formatWineryScore(winery.overall_score)}</strong>
            {" · "}
            {dataCoverage(winery)}
          </span>
        </div>
        <WeightControls weights={weights} onChange={setWeights} />
        <ScoreBreakdown winery={winery} />
      </Card>

      <LandRiskCard check={winery.land_check} />

      <Card className="p-5 space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Estimate</h2>
        <AcquisitionEstimate
          statedCases={winery.production_cases}
          bottlePrice={winery.median_bottle_price}
          askingPrice={winery.asking_price}
        />
      </Card>

      <Card className="p-5 space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Linked wines ({winery.wines.length})</h2>
        {winery.wines.length === 0 ? (
          <p className="text-sm text-gray-500">
            No wines are linked. This winery may sell only direct, or its products may use a different brand name.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-200">
                  <th className="py-2 pr-3 font-medium">Wine</th>
                  <th className="py-2 pr-3 font-medium">Style</th>
                  <th className="py-2 pr-3 font-medium">Shelf price (CAD)</th>
                  <th className="py-2 pr-3 font-medium">Size</th>
                  <th className="py-2 pr-3 font-medium">Critic score</th>
                  <th className="py-2 font-medium">Historical USD</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {winery.wines.map((wine) => (
                  <tr key={wine.id}>
                    <td className="py-2 pr-3 text-gray-800">{wine.name}</td>
                    <td className="py-2 pr-3 text-gray-600">{wine.style ?? "—"}</td>
                    <td className="py-2 pr-3">{wine.retail_price_cad != null ? formatPrice(wine.retail_price_cad, "CAD") : "—"}</td>
                    <td className="py-2 pr-3 text-gray-600">{wine.litres != null ? `${wine.litres * 1000} ml` : "—"}</td>
                    <td className="py-2 pr-3">{wine.critic_score ?? "—"}</td>
                    <td className="py-2">{wine.historical_price_usd != null ? formatPrice(wine.historical_price_usd, "USD") : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card className="p-5 space-y-2">
        <h2 className="text-xl font-semibold text-gray-800">Sources</h2>
        <ul className="text-sm text-gray-600 space-y-1">
          {winery.sources.map((source) => (
            <li key={source.label}>
              {source.url ? <a href={source.url} target="_blank" rel="noreferrer" className="underline">{source.label}</a> : source.label}
              {source.as_of && ` · as of ${source.as_of}`}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
