"use client";

import { useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { SearchBar } from "@/components/wine/SearchBar";
import { WineCard } from "@/components/wine/WineCard";
import { SearchFilters, WineSearchResult } from "@/types/wine";
import { searchWines } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { ChevronLeft, ChevronRight, AlertCircle } from "lucide-react";

export default function SearchPage() {
  const router = useRouter();
  const [results, setResults] = useState<WineSearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFilters, setLastFilters] = useState<SearchFilters>({ q: "" });
  const PER_PAGE = 20;

  const handleSearch = useCallback(async (filters: SearchFilters, p = 1) => {
    setLoading(true);
    setError(null);
    setLastFilters(filters);
    setPage(p);
    try {
      const data = await searchWines(filters, p, PER_PAGE);
      setResults(data.results);
      setTotal(data.total);
    } catch {
      setError("Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const totalPages = Math.ceil(total / PER_PAGE);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Search Wines</h1>
        <p className="text-gray-500">Find wines by name, producer, region, grape, or vintage.</p>
      </div>

      <SearchBar onSearch={(f) => handleSearch(f, 1)} loading={loading} />

      {error && (
        <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * PER_PAGE + 1}–{Math.min(page * PER_PAGE, total)} of{" "}
            <strong>{total}</strong> results
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            {results.map((wine) => (
              <WineCard key={wine.id} wine={wine} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 pt-4">
              <Button
                variant="ghost"
                size="sm"
                disabled={page <= 1}
                onClick={() => handleSearch(lastFilters, page - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              <span className="text-sm text-gray-500">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="ghost"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => handleSearch(lastFilters, page + 1)}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      )}

      {!loading && results.length === 0 && total === 0 && lastFilters.q && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg font-medium">No wines found</p>
          <p className="text-sm mt-1">Try a different search term or adjust your filters.</p>
        </div>
      )}

      {!loading && results.length === 0 && !lastFilters.q && (
        <div className="text-center py-16 text-gray-300">
          <p className="text-lg">Search for a wine above to get started.</p>
        </div>
      )}
    </div>
  );
}
