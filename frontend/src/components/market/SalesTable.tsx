import { formatPrice } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { MarketData } from "@/types/winery";

export function SalesTable({ market }: { market: MarketData }) {
  return (
  <Card className="p-5 space-y-4">
    <h2 className="text-xl font-semibold text-gray-800">Reported winery sales</h2>
    <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
      Not a price guide. These are the few prices made public, from 2017 to 2026. Court-ordered sales are often distressed, and what each sale included varies. Check the evidence before relying on a figure.
    </p>
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 border-b border-gray-200">
            <th className="py-2 pr-3 font-medium">Sale</th>
            <th className="py-2 pr-3 font-medium">Year</th>
            <th className="py-2 pr-3 font-medium">Sale price</th>
            <th className="py-2 pr-3 font-medium">Last asking</th>
            <th className="py-2 pr-3 font-medium">Sale / asking</th>
            <th className="py-2 pr-3 font-medium">Planted / total acres</th>
            <th className="py-2 font-medium">Type and evidence</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {market.sales.map((sale) => (
            <tr key={sale.id}>
              <td className="py-2 pr-3">
                <span className="font-medium text-gray-800">{sale.name}</span>
                {sale.location && <div className="text-xs text-gray-500">{sale.location}</div>}
                {sale.notes && <div className="mt-1 max-w-xl text-xs text-gray-600">{sale.notes}</div>}
              </td>
              <td className="py-2 pr-3">{sale.sold_year}</td>
              <td className="py-2 pr-3 whitespace-nowrap">{formatPrice(sale.sale_price, "CAD")}</td>
              <td className="py-2 pr-3 whitespace-nowrap">{sale.last_asking_price != null ? formatPrice(sale.last_asking_price, "CAD") : "Not stated"}</td>
              <td className="py-2 pr-3">{sale.share_of_asking != null ? `${Math.round(sale.share_of_asking * 100)}%` : "—"}</td>
              <td className="py-2 pr-3">{sale.planted_acres ?? "?"} / {sale.total_acres ?? "?"}</td>
              <td className="py-2 text-gray-600">
                <div>{sale.sale_type}</div>
                <div className="text-xs">{sale.evidence}</div>
                {sale.source_url && <a href={sale.source_url} target="_blank" rel="noreferrer" className="text-xs underline">Source</a>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </Card>
  );
}
