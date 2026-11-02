import { Card } from "@/components/ui/Card";
import { MarketData } from "@/types/winery";

export function RecheckList({ market }: { market: MarketData }) {
  if (market.listings_to_recheck.length === 0) return null;

  return (
    <Card className="p-5 space-y-3">
      <h2 className="text-xl font-semibold text-gray-800">Listings to re-check</h2>
      <p className="text-sm text-gray-500">
        Open listings last checked {market.recheck_after_days} or more days ago, oldest first. Anything may have sold or changed price.
      </p>
      <ul className="space-y-1 text-sm">
        {market.listings_to_recheck.map((listing) => (
          <li key={listing.id} className="flex flex-wrap justify-between gap-2 border-b border-gray-100 py-1">
            {listing.source_url ? (
              <a href={listing.source_url} target="_blank" rel="noreferrer" className="underline text-gray-800">{listing.advertised_name}</a>
            ) : (
              <span className="text-gray-800">{listing.advertised_name}</span>
            )}
            <span className="text-gray-500">Last checked {listing.as_of}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
