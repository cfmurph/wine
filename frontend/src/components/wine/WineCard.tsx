"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import { MapPin, Star, DollarSign, Wine } from "lucide-react";
import { WineSearchResult } from "@/types/wine";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatPrice, formatScore, getStyleColor } from "@/lib/utils";

interface WineCardProps {
  wine: WineSearchResult;
  onSelect?: (id: string) => void;
  selected?: boolean;
}

export function WineCard({ wine, onSelect, selected }: WineCardProps) {
  const router = useRouter();

  const handleClick = () => {
    if (onSelect) {
      onSelect(wine.id);
    } else {
      router.push(`/wine/${wine.id}`);
    }
  };

  return (
    <Card
      onClick={handleClick}
      className={selected ? "ring-2 ring-wine-500 border-wine-300" : undefined}
    >
      <div className="flex gap-4 p-4">
        <div className="w-16 h-20 flex-shrink-0 relative rounded-lg overflow-hidden bg-gray-50 border border-gray-100">
          {wine.image_url ? (
            <Image
              src={wine.image_url}
              alt={wine.canonical_name}
              fill
              className="object-contain p-1"
              sizes="64px"
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <Wine className="h-8 w-8 text-wine-200" />
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-gray-900 leading-snug line-clamp-2">
              {wine.canonical_name}
              {wine.vintage && (
                <span className="ml-1.5 text-gray-500 font-normal">{wine.vintage}</span>
              )}
            </h3>
            {wine.style && (
              <Badge className={getStyleColor(wine.style)}>{wine.style}</Badge>
            )}
          </div>

          {wine.producer && (
            <p className="text-sm text-gray-500 mt-0.5 truncate">{wine.producer}</p>
          )}

          <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
            {(wine.country || wine.region) && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {[wine.region, wine.country].filter(Boolean).join(", ")}
              </span>
            )}
          </div>

          <div className="flex items-center gap-4 mt-2">
            {wine.avg_score != null && (
              <span className="flex items-center gap-1 text-sm font-semibold text-wine-700">
                <Star className="h-4 w-4 fill-current" />
                {formatScore(wine.avg_score)}
                <span className="font-normal text-gray-400">/100</span>
              </span>
            )}
            {wine.avg_price != null && (
              <span className="flex items-center gap-1 text-sm font-semibold text-gray-700">
                <DollarSign className="h-3.5 w-3.5" />
                {formatPrice(wine.avg_price, wine.currency)}
              </span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
