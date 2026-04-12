"use client";

import { useState } from "react";
import { GitCompare, Plus, X, Star, DollarSign, Trophy } from "lucide-react";
import { CompareItem, WineSearchResult } from "@/types/wine";
import { compareWines, searchWines } from "@/lib/api";
import { WineCard } from "@/components/wine/WineCard";
import { SearchBar } from "@/components/wine/SearchBar";
import { Button } from "@/components/ui/Button";
import { formatPrice, formatScore } from "@/lib/utils";

export default function ComparePage() {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<WineSearchResult[]>([]);
  const [compareData, setCompareData] = useState<CompareItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (filters: { q: string; [k: string]: unknown }) => {
    setLoading(true);
    try {
      const data = await searchWines(filters as any, 1, 10);
      setSearchResults(data.results);
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id)
        ? prev.filter((x) => x !== id)
        : prev.length < 4
        ? [...prev, id]
        : prev
    );
  };

  const handleCompare = async () => {
    if (selectedIds.length < 2) return;
    setComparing(true);
    setError(null);
    try {
      const data = await compareWines(selectedIds);
      setCompareData(data.wines);
      setSearchResults([]);
    } catch {
      setError("Comparison failed. Make sure the wines exist in the database.");
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <GitCompare className="h-8 w-8 text-wine-700" />
          Compare Wines
        </h1>
        <p className="text-gray-500">Select 2–4 wines to compare side by side.</p>
      </div>

      {/* Search to add wines */}
      {!compareData && (
        <div className="space-y-4">
          <SearchBar onSearch={handleSearch} loading={loading} />

          {selectedIds.length > 0 && (
            <div className="flex items-center gap-3 p-4 bg-wine-50 border border-wine-200 rounded-xl">
              <span className="text-sm font-medium text-wine-800">
                {selectedIds.length} wine{selectedIds.length > 1 ? "s" : ""} selected
                {selectedIds.length < 2 && " (select at least 2)"}
              </span>
              <Button
                size="sm"
                onClick={handleCompare}
                disabled={selectedIds.length < 2 || comparing}
              >
                {comparing ? "Comparing…" : "Compare now"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setSelectedIds([])}
              >
                Clear
              </Button>
            </div>
          )}

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
              {error}
            </p>
          )}

          {searchResults.length > 0 && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">Click a wine to select it for comparison:</p>
              <div className="grid gap-3 sm:grid-cols-2">
                {searchResults.map((wine) => (
                  <WineCard
                    key={wine.id}
                    wine={wine}
                    onSelect={toggleSelect}
                    selected={selectedIds.includes(wine.id)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Comparison table */}
      {compareData && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-800">Comparison Results</h2>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => { setCompareData(null); setSelectedIds([]); }}
            >
              <X className="h-4 w-4" />
              Start over
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-wine-900 text-white">
                  <th className="text-left px-4 py-3 rounded-tl-xl font-medium w-32">Property</th>
                  {compareData.map((w) => (
                    <th key={w.id} className="text-left px-4 py-3 font-medium">
                      <div className="font-semibold">{w.canonical_name}</div>
                      {w.vintage && <div className="text-wine-300 font-normal">{w.vintage}</div>}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  {
                    label: "Producer",
                    render: (w: CompareItem) => w.producer ?? "—",
                  },
                  {
                    label: "Region",
                    render: (w: CompareItem) =>
                      [w.region, w.country].filter(Boolean).join(", ") || "—",
                  },
                  {
                    label: "Style",
                    render: (w: CompareItem) => w.style ?? "—",
                  },
                  {
                    label: "Grapes",
                    render: (w: CompareItem) => w.grape_varieties?.join(", ") || "—",
                  },
                  {
                    label: "Avg Score",
                    render: (w: CompareItem, isMax: boolean) => (
                      <span className={`flex items-center gap-1 font-bold ${isMax ? "text-wine-700" : ""}`}>
                        {isMax && <Trophy className="h-4 w-4" />}
                        <Star className="h-3.5 w-3.5 fill-current text-wine-400" />
                        {w.avg_score != null ? `${formatScore(w.avg_score)}/100` : "—"}
                      </span>
                    ),
                    isMaxFn: (wines: CompareItem[]) => {
                      const max = Math.max(...wines.map((w) => w.avg_score ?? 0));
                      return wines.map((w) => w.avg_score === max && max > 0);
                    },
                  },
                  {
                    label: "Avg Price",
                    render: (w: CompareItem, isMin: boolean) => (
                      <span className={`flex items-center gap-1 font-bold ${isMin ? "text-green-700" : ""}`}>
                        {isMin && <Trophy className="h-4 w-4" />}
                        {w.avg_price != null ? formatPrice(w.avg_price, w.currency) : "—"}
                      </span>
                    ),
                    isMaxFn: (wines: CompareItem[]) => {
                      const min = Math.min(...wines.filter((w) => w.avg_price != null).map((w) => w.avg_price!));
                      return wines.map((w) => w.avg_price === min && min > 0);
                    },
                  },
                  {
                    label: "Value Score",
                    render: (w: CompareItem, isMax: boolean) => (
                      <span className={`font-bold ${isMax ? "text-purple-700" : ""}`}>
                        {w.value_score != null ? w.value_score.toFixed(2) : "—"}
                      </span>
                    ),
                    isMaxFn: (wines: CompareItem[]) => {
                      const max = Math.max(...wines.map((w) => w.value_score ?? 0));
                      return wines.map((w) => w.value_score === max && max > 0);
                    },
                  },
                ].map(({ label, render, isMaxFn }, rowIdx) => {
                  const highlights = isMaxFn ? isMaxFn(compareData) : compareData.map(() => false);
                  return (
                    <tr key={label} className={rowIdx % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                      <td className="px-4 py-3 font-medium text-gray-600">{label}</td>
                      {compareData.map((w, i) => (
                        <td key={w.id} className="px-4 py-3 text-gray-700">
                          {render(w, highlights[i])}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
