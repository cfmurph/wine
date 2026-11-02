"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertCircle, GitCompare, Grape } from "lucide-react";
import { getWineries } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { dataCoverage, formatWineryScore, ScreeningNotice } from "@/components/winery/ScoreBreakdown";
import { WeightControls } from "@/components/winery/WeightControls";
import { DEFAULT_WEIGHTS, WineryFilters, WinerySummary } from "@/types/winery";

type SortKey = "overall_score" | "name" | "region" | "asking_price" | "median_bottle_price" | "avg_critic_score";

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: "name", label: "Winery" },
  { key: "region", label: "Region" },
  { key: "overall_score", label: "Score" },
  { key: "asking_price", label: "Asking" },
  { key: "median_bottle_price", label: "Median bottle" },
  { key: "avg_critic_score", label: "Critics" },
];

const SEARCH_DELAY_MS = 300;
const MAX_COMPARE = 4;

export default function WineriesPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<WineryFilters>({
    q: "", region: "", forSale: false, minAsking: "", maxAsking: "", minCases: "",
  });
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [results, setResults] = useState<WinerySummary[]>([]);
  const [regions, setRegions] = useState<string[]>([]);
  const [sort, setSort] = useState<{ key: SortKey; descending: boolean }>({ key: "overall_score", descending: true });
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let current = true;
    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getWineries(filters, weights);
        if (!current) return;
        setResults(data.results);
        setRegions(data.regions);
      } catch {
        if (current) setError("Couldn't load wineries. Please try again.");
      } finally {
        if (current) setLoading(false);
      }
    }, SEARCH_DELAY_MS);
    return () => {
      current = false;
      clearTimeout(timer);
    };
  }, [filters, weights]);

  const sorted = useMemo(() => {
    const direction = sort.descending ? -1 : 1;
    return [...results].sort((a, b) => {
      const left = a[sort.key];
      const right = b[sort.key];
      // Unknown values stay at the bottom in either direction.
      if (left == null) return right == null ? a.name.localeCompare(b.name) : 1;
      if (right == null) return -1;
      if (typeof left === "string") return direction * left.localeCompare(String(right));
      return direction * (left - Number(right));
    });
  }, [results, sort]);

  const toggleSort = (key: SortKey) =>
    setSort((previous) =>
      previous.key === key ? { key, descending: !previous.descending } : { key, descending: key === "overall_score" }
    );

  const toggleSelected = (id: string) =>
    setSelected((previous) =>
      previous.includes(id)
        ? previous.filter((x) => x !== id)
        : previous.length < MAX_COMPARE
        ? [...previous, id]
        : previous
    );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <Grape className="h-8 w-8 text-wine-700" />
          Winery Candidates
        </h1>
        <p className="text-gray-500">Screen licensed BC wineries as possible acquisitions.</p>
      </div>

      <ScreeningNotice />

      <Card className="p-4 space-y-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <Input
            id="winery-q"
            label="Name or city"
            value={filters.q}
            onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          />
          <div className="space-y-1">
            <label htmlFor="winery-region" className="block text-sm font-medium text-gray-700">
              Region
            </label>
            <select
              id="winery-region"
              value={filters.region}
              onChange={(e) => setFilters({ ...filters, region: e.target.value })}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-wine-500 focus:outline-none focus:ring-1 focus:ring-wine-500"
            >
              <option value="">All regions</option>
              {regions.map((region) => (
                <option key={region} value={region}>{region}</option>
              ))}
            </select>
          </div>
          <Input
            id="winery-min-asking"
            label="Min asking ($)"
            type="number"
            min={0}
            value={filters.minAsking}
            onChange={(e) => setFilters({ ...filters, minAsking: e.target.value })}
          />
          <Input
            id="winery-max-asking"
            label="Max asking ($)"
            type="number"
            min={0}
            value={filters.maxAsking}
            onChange={(e) => setFilters({ ...filters, maxAsking: e.target.value })}
          />
          <Input
            id="winery-min-cases"
            label="Min cases"
            type="number"
            min={0}
            value={filters.minCases}
            onChange={(e) => setFilters({ ...filters, minCases: e.target.value })}
          />
        </div>
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <input
            type="checkbox"
            checked={filters.forSale}
            onChange={(e) => setFilters({ ...filters, forSale: e.target.checked })}
            className="accent-wine-700"
          />
          Only wineries still for sale
        </label>
        <WeightControls weights={weights} onChange={setWeights} />
      </Card>

      {error && (
        <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-gray-500">
          {loading ? "Loading…" : <><strong>{results.length}</strong> wineries</>}
        </p>
        <Button
          size="sm"
          disabled={selected.length < 2}
          onClick={() => router.push(`/wineries/compare?ids=${selected.join(",")}`)}
        >
          <GitCompare className="h-4 w-4" />
          Compare {selected.length ? `(${selected.length})` : "2–4"}
        </Button>
      </div>

      <div className="overflow-x-auto bg-white rounded-xl border border-gray-100 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-wine-900 text-white text-left">
              <th className="px-3 py-3"><span className="sr-only">Select</span></th>
              {COLUMNS.map(({ key, label }) => (
                <th key={key} className="px-3 py-3 font-medium whitespace-nowrap" aria-sort={sort.key === key ? (sort.descending ? "descending" : "ascending") : "none"}>
                  <button onClick={() => toggleSort(key)} className="hover:underline">
                    {label}
                    {sort.key === key && (sort.descending ? " ↓" : " ↑")}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sorted.map((winery) => (
              <tr key={winery.id} className="hover:bg-wine-50">
                <td className="px-3 py-2">
                  <input
                    type="checkbox"
                    aria-label={`Select ${winery.name} to compare`}
                    checked={selected.includes(winery.id)}
                    disabled={!selected.includes(winery.id) && selected.length >= MAX_COMPARE}
                    onChange={() => toggleSelected(winery.id)}
                    className="accent-wine-700"
                  />
                </td>
                <td className="px-3 py-2">
                  <Link href={`/wineries/${winery.id}`} className="font-medium text-wine-800 hover:underline">
                    {winery.name}
                  </Link>
                  {winery.city && <div className="text-xs text-gray-500">{winery.city}</div>}
                </td>
                <td className="px-3 py-2 text-gray-600">{winery.region ?? "Unknown"}</td>
                <td className="px-3 py-2 whitespace-nowrap">
                  <strong>{formatWineryScore(winery.overall_score)}</strong>
                  <div className="text-xs text-gray-500">{dataCoverage(winery)}</div>
                </td>
                <td className="px-3 py-2 whitespace-nowrap">
                  {winery.asking_price != null ? formatPrice(winery.asking_price, "CAD") : "—"}
                  {winery.listing_status && <div><Badge variant="wine">{winery.listing_status}</Badge></div>}
                </td>
                <td className="px-3 py-2">{winery.median_bottle_price != null ? formatPrice(winery.median_bottle_price, "CAD") : "—"}</td>
                <td className="px-3 py-2">{winery.avg_critic_score ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && sorted.length === 0 && !error && (
          <p className="text-center py-12 text-gray-400">No wineries match these filters.</p>
        )}
      </div>
    </div>
  );
}
