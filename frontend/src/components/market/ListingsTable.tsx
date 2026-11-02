import Link from "next/link";
import { formatPrice } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { MarketData } from "@/types/winery";

export function ListingsTable({ market }: { market: MarketData }) {
  return (
  <Card className="p-5 space-y-4">
    <h2 className="text-xl font-semibold text-gray-800">Winery sale listings</h2>
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 border-b border-gray-200">
            <th className="py-2 pr-3 font-medium">Listing</th>
            <th className="py-2 pr-3 font-medium">Asking price</th>
            <th className="py-2 pr-3 font-medium">Planted / total acres</th>
            <th className="py-2 pr-3 font-medium">Status</th>
            <th className="py-2 font-medium">As of</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {market.listings.map((listing) => (
            <tr key={listing.id}>
              <td className="py-2 pr-3">
                {listing.winery_id ? (
                  <Link href={`/wineries/${listing.winery_id}`} className="font-medium text-wine-800 hover:underline">{listing.advertised_name}</Link>
                ) : (
                  <span className="font-medium text-gray-800">{listing.advertised_name}</span>
                )}
                {listing.location && <div className="text-xs text-gray-500">{listing.location}</div>}
                {!listing.winery_id && <div className="text-xs text-gray-500">Not matched to an active winery licence</div>}
                {listing.notes && <div className="mt-1 max-w-xl text-xs text-gray-600">{listing.notes}</div>}
              </td>
              <td className="py-2 pr-3 whitespace-nowrap">{listing.asking_price != null ? formatPrice(listing.asking_price, listing.currency) : "Not stated"}</td>
              <td className="py-2 pr-3">{listing.planted_acres ?? "?"} / {listing.total_acres ?? "?"}</td>
              <td className="py-2 pr-3">{listing.status && <Badge variant="wine">{listing.status}</Badge>}</td>
              <td className="py-2 whitespace-nowrap text-gray-600">
                {listing.as_of ?? "—"}
                {listing.source_url && <div><a href={listing.source_url} target="_blank" rel="noreferrer" className="text-xs underline">Source</a></div>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    <p className="text-xs text-gray-500">
      Asking prices, entered by hand from public sources, with any reported sale price in the notes. &quot;As of&quot; is the date last checked. Listings change, so confirm details with the listing agent.
    </p>
  </Card>
  );
}
