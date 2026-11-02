"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowLeft, GitCompare } from "lucide-react";
import { compareWineries } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { dataCoverage, formatWineryScore, ScreeningNotice } from "@/components/winery/ScoreBreakdown";
import { WeightControls } from "@/components/winery/WeightControls";
import { DEFAULT_WEIGHTS, SCORE_LABELS, ScoreName, WineryDetail } from "@/types/winery";

const cad = (value?: number | null) => (value != null ? formatPrice(value, "CAD") : "Unknown");
const stated = (value?: boolean | null) => (value == null ? "Not stated" : value ? "Yes" : "No");

const ROWS: { label: string; render: (winery: WineryDetail) => React.ReactNode }[] = [
  { label: "Location", render: (w) => [w.city, w.region].filter(Boolean).join(", ") || "Unknown" },
  { label: "Overall score", render: (w) => <strong>{formatWineryScore(w.overall_score)}</strong> },
  { label: "Data coverage", render: dataCoverage },
  ...(Object.keys(SCORE_LABELS) as ScoreName[]).map((name) => ({
    label: `${SCORE_LABELS[name]} score`,
    render: (w: WineryDetail) =>
      `${formatWineryScore(w.sub_scores[name].score)} (${w.sub_scores[name].available}/${w.sub_scores[name].total})`,
  })),
  { label: "Asking price", render: (w) => cad(w.asking_price) },
  { label: "Listing status", render: (w) => w.listing_status ?? "No listing found" },
  { label: "Planted acres", render: (w) => w.listings[0]?.planted_acres ?? "Unknown" },
  { label: "Licence included", render: (w) => (w.listings[0] ? stated(w.listings[0].includes_licence) : "—") },
  { label: "Brand included", render: (w) => (w.listings[0] ? stated(w.listings[0].includes_brand) : "—") },
  { label: "Cases (actual or stated capacity)", render: (w) => w.production_cases?.toLocaleString() ?? "Unknown" },
  { label: "Median 750 ml shelf price", render: (w) => cad(w.median_bottle_price) },
  { label: "Average critic score (historical)", render: (w) => w.avg_critic_score ?? "Unknown" },
  { label: "Linked wines", render: (w) => w.wine_count },
  { label: "Licensed service capacity", render: (w) => w.service_capacity ?? "Unknown" },
];

function Comparison() {
  const ids = useSearchParams().get("ids") ?? "";
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [wineries, setWineries] = useState<WineryDetail[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const wineryIds = ids.split(",").filter(Boolean);
    if (wineryIds.length < 2 || wineryIds.length > 4) {
      setError("Select 2–4 wineries from the list to compare them.");
      return;
    }
    let current = true;
    setError(null);
    compareWineries(wineryIds, weights)
      .then((data) => {
        if (current) setWineries(data);
      })
      .catch(() => {
        if (current) setError("Comparison failed. Please try again.");
      });
    return () => {
      current = false;
    };
  }, [ids, weights]);

  if (error) return <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">{error}</p>;
  if (!wineries) return <p className="text-gray-400 py-16 text-center">Loading…</p>;

  return (
    <>
      <Card className="p-4"><WeightControls weights={weights} onChange={setWeights} /></Card>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-wine-900 text-white text-left">
              <th className="px-4 py-3 font-medium w-56">Property</th>
              {wineries.map((winery) => (
                <th key={winery.id} className="px-4 py-3 font-semibold">
                  <Link href={`/wineries/${winery.id}`} className="hover:underline">{winery.name}</Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map(({ label, render }, index) => (
              <tr key={label} className={index % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-4 py-3 font-medium text-gray-600">{label}</td>
                {wineries.map((winery) => (
                  <td key={winery.id} className="px-4 py-3 text-gray-700">{render(winery)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default function CompareWineriesPage() {
  return (
    <div className="space-y-6">
      <div>
        <Link href="/wineries" className="text-sm text-wine-700 hover:underline inline-flex items-center gap-1 mb-3">
          <ArrowLeft className="h-4 w-4" />
          All wineries
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
          <GitCompare className="h-8 w-8 text-wine-700" />
          Compare Wineries
        </h1>
      </div>
      <ScreeningNotice />
      <Suspense fallback={<p className="text-gray-400 py-16 text-center">Loading…</p>}>
        <Comparison />
      </Suspense>
    </div>
  );
}
