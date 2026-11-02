import { formatPrice } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { SourceLink } from "@/components/market/SourceLink";
import { MarketData } from "@/types/winery";

export function ShelfPrices({ market }: { market: MarketData }) {
  const largestBucket = Math.max(0, ...market.price_buckets.map((b) => b.count));

  return (
  <Card className="p-5 space-y-4">
    <h2 className="text-xl font-semibold text-gray-800">BC wine shelf prices (750 ml)</h2>
    <p className="text-sm text-gray-500">
      Median {market.median_bottle_price != null ? formatPrice(market.median_bottle_price, "CAD") : "unknown"} across {market.priced_bottles} products.
    </p>
    <div className="space-y-2">
      {market.price_buckets.map((bucket) => (
        <div key={bucket.label} className="flex items-center gap-3 text-sm">
          <span className="w-20 text-gray-600">{bucket.label}</span>
          <div className="flex-1 h-3 rounded-full bg-gray-100 overflow-hidden">
            <div className="h-full bg-wine-600" style={{ width: `${(bucket.count / (largestBucket || 1)) * 100}%` }} />
          </div>
          <span className="w-10 text-right text-gray-600">{bucket.count}</span>
        </div>
      ))}
    </div>
    <p className="text-xs text-gray-500">
      <SourceLink source={market.price_source} />{market.price_date && ` · as of ${market.price_date}`}. Counts products listed, not bottles sold.
    </p>
  </Card>
  );
}
