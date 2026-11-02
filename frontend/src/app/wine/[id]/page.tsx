"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import {
  MapPin, Wine, Star, DollarSign, Utensils,
  BookMarked, AlertCircle, ArrowLeft,
} from "lucide-react";
import { useFetch } from "@/hooks/useFetch";
import { getWineDetail, addToCellar } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { formatPrice, formatScore, getStyleColor } from "@/lib/utils";

export default function WineDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: wine, failed, loading } = useFetch(id, () => getWineDetail(id));
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleSave = async (status: "favorite" | "cellar" | "want_to_try" | "tried") => {
    try {
      await addToCellar({ wine_id: id, status });
      setSaveStatus(`Saved as "${status.replace("_", " ")}"`);
      setTimeout(() => setSaveStatus(null), 3000);
    } catch {
      setSaveStatus("Please log in to save wines.");
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  if (loading) return <WineDetailSkeleton />;
  if (failed || !wine) return <ErrorState message={failed ? "Could not load wine details." : "Wine not found"} />;

  const avgScore = wine.scores.length
    ? wine.scores.reduce((s, r) => s + (r.score ?? 0), 0) / wine.scores.filter((r) => r.score).length
    : null;

  const priceRange = wine.prices.length
    ? wine.prices[0]
    : null;

  return (
    <div className="space-y-8">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      {/* Hero section */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="flex flex-col md:flex-row gap-8 p-6 md:p-8">
          {/* Bottle image */}
          <div className="w-32 h-48 md:w-40 md:h-60 flex-shrink-0 mx-auto md:mx-0 relative rounded-xl overflow-hidden bg-gray-50 border border-gray-100">
            {wine.image_url ? (
              <Image
                src={wine.image_url}
                alt={wine.canonical_name}
                fill
                className="object-contain p-2"
                sizes="160px"
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <Wine className="h-16 w-16 text-wine-200" />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 space-y-4">
            <div className="flex flex-wrap items-start gap-3">
              <h1 className="text-3xl font-bold text-gray-900 flex-1">
                {wine.canonical_name}
                {wine.vintage && (
                  <span className="ml-2 text-xl font-normal text-gray-400">{wine.vintage}</span>
                )}
              </h1>
              {wine.style && (
                <Badge className={getStyleColor(wine.style)} variant="default">
                  {wine.style}
                </Badge>
              )}
            </div>

            {wine.producer && (
              <p className="text-lg text-gray-600">{wine.producer}</p>
            )}

            <div className="flex flex-wrap gap-4 text-sm text-gray-500">
              {(wine.country || wine.region) && (
                <span className="flex items-center gap-1.5">
                  <MapPin className="h-4 w-4" />
                  {[wine.appellation, wine.region, wine.country].filter(Boolean).join(", ")}
                </span>
              )}
              {wine.abv && (
                <span className="flex items-center gap-1.5">
                  <Wine className="h-4 w-4" />
                  {wine.abv}% ABV
                </span>
              )}
            </div>

            {wine.grape_varieties?.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {wine.grape_varieties.map((g) => (
                  <Badge key={g} variant="wine">{g}</Badge>
                ))}
              </div>
            )}

            {/* Score + Price summary */}
            <div className="flex gap-6">
              {avgScore != null && (
                <div className="text-center">
                  <div className="flex items-center gap-1 text-2xl font-bold text-wine-700">
                    <Star className="h-5 w-5 fill-current" />
                    {formatScore(avgScore)}
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">Avg score /100</p>
                </div>
              )}
              {priceRange && (
                <div className="text-center">
                  <div className="flex items-center gap-1 text-2xl font-bold text-gray-700">
                    <DollarSign className="h-5 w-5" />
                    {formatPrice(priceRange.avg_price, priceRange.currency)}
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">Avg price</p>
                </div>
              )}
            </div>

            {/* Save actions */}
            <div className="flex flex-wrap gap-2 pt-2">
              <Button size="sm" onClick={() => handleSave("favorite")}>
                <BookMarked className="h-4 w-4" />
                Save favorite
              </Button>
              <Button size="sm" variant="secondary" onClick={() => handleSave("want_to_try")}>
                Want to try
              </Button>
              <Button size="sm" variant="secondary" onClick={() => handleSave("cellar")}>
                Add to cellar
              </Button>
            </div>
            {saveStatus && (
              <p className="text-sm text-wine-700 font-medium">{saveStatus}</p>
            )}
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Description */}
        {wine.description && (
          <Card className="md:col-span-2 lg:col-span-3 p-6">
            <h2 className="font-semibold text-gray-700 mb-2">About this wine</h2>
            <p className="text-gray-600 leading-relaxed">{wine.description}</p>
          </Card>
        )}

        {/* Scores */}
        {wine.scores.length > 0 && (
          <Card className="p-6 space-y-3">
            <h2 className="font-semibold text-gray-700 flex items-center gap-2">
              <Star className="h-4 w-4 text-wine-600" />
              Critic Scores
            </h2>
            {wine.scores.map((score) => (
              <div key={score.provider} className="flex items-center justify-between text-sm">
                <span className="text-gray-500 capitalize">
                  {score.provider.replace(/_/g, " ")}
                </span>
                <span className="font-bold text-wine-700">
                  {score.score != null ? `${score.score}/${score.score_scale}` : "—"}
                </span>
              </div>
            ))}
          </Card>
        )}

        {/* Prices */}
        {wine.prices.length > 0 && (
          <Card className="p-6 space-y-3">
            <h2 className="font-semibold text-gray-700 flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-green-600" />
              Pricing
            </h2>
            {wine.prices.map((price) => (
              <div key={price.provider} className="space-y-1">
                <p className="text-xs text-gray-400 capitalize">
                  {price.provider.replace(/_/g, " ")}
                </p>
                <div className="grid grid-cols-3 gap-1 text-sm text-center">
                  <div>
                    <p className="text-gray-500 text-xs">Min</p>
                    <p className="font-medium">{formatPrice(price.min_price, price.currency)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Avg</p>
                    <p className="font-bold text-gray-900">{formatPrice(price.avg_price, price.currency)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-xs">Max</p>
                    <p className="font-medium">{formatPrice(price.max_price, price.currency)}</p>
                  </div>
                </div>
                {price.purchase_url && (
                  <a
                    href={price.purchase_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-wine-600 hover:underline"
                  >
                    Buy now →
                  </a>
                )}
              </div>
            ))}
          </Card>
        )}

        {/* Food pairings */}
        {wine.pairings.length > 0 && (
          <Card className="p-6 space-y-3">
            <h2 className="font-semibold text-gray-700 flex items-center gap-2">
              <Utensils className="h-4 w-4 text-orange-500" />
              Food Pairings
            </h2>
            <div className="flex flex-wrap gap-2">
              {wine.pairings.map((food) => (
                <Badge key={food} variant="outline" className="capitalize">
                  {food}
                </Badge>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

function WineDetailSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-5 w-16 bg-gray-200 rounded" />
      <div className="bg-white rounded-2xl border border-gray-100 p-8 h-64" />
      <div className="grid md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-xl border border-gray-100 h-40" />
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="text-center py-24 space-y-3">
      <AlertCircle className="h-10 w-10 text-red-400 mx-auto" />
      <p className="text-gray-600">{message}</p>
    </div>
  );
}
