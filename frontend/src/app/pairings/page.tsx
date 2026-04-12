"use client";

import { useState } from "react";
import { Utensils, Wine, Search } from "lucide-react";
import { PairingSearchResponse, WineSearchResult } from "@/types/wine";
import { getPairings } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { WineCard } from "@/components/wine/WineCard";
import { Badge } from "@/components/ui/Badge";

export default function PairingsPage() {
  const [food, setFood] = useState("");
  const [result, setResult] = useState<PairingSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!food.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getPairings(food.trim());
      setResult(data);
    } catch {
      setError("Pairing lookup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <Utensils className="h-8 w-8 text-orange-500" />
          Food & Wine Pairing
        </h1>
        <p className="text-gray-500">Enter a dish and get wine pairing suggestions.</p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-3 max-w-lg">
        <div className="relative flex-1">
          <Utensils className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={food}
            onChange={(e) => setFood(e.target.value)}
            placeholder="e.g. steak, salmon, truffle pasta…"
            className="w-full pl-9 pr-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-wine-500"
          />
        </div>
        <Button type="submit" disabled={loading || !food.trim()}>
          {loading ? "Looking…" : "Find pairings"}
        </Button>
      </form>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          {error}
        </p>
      )}

      {result && (
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-800 mb-3">
              Wine styles that pair with{" "}
              <span className="text-wine-700">{result.food}</span>
            </h2>
            <div className="flex flex-wrap gap-2">
              {result.wine_types.map((type) => (
                <Badge key={type} variant="wine" className="text-sm px-3 py-1 capitalize">
                  <Wine className="h-3.5 w-3.5 mr-1.5 inline" />
                  {type.replace(/_/g, " ")}
                </Badge>
              ))}
            </div>
          </div>

          {result.wines.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-gray-800 mb-3">Recommended bottles</h2>
              <div className="grid gap-3 sm:grid-cols-2">
                {result.wines.map((wine) => (
                  <WineCard key={wine.id} wine={wine} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
