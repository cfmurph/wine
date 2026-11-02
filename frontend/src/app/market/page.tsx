"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, BarChart3 } from "lucide-react";
import { getMarket } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { DataSource, MarketData, MarketStat } from "@/types/winery";

const RECENT_PERIODS = 10;
const BC = "British Columbia";

function SourceLink({ source }: { source: DataSource }) {
  return source.url ? (
    <a href={source.url} target="_blank" rel="noreferrer" className="underline">{source.label}</a>
  ) : (
    <>{source.label}</>
  );
}

function findStat(stats: MarketStat[], period: string, geography: string, metric: MarketStat["metric"]) {
  return stats.find((s) => s.period === period && s.geography === geography && s.metric === metric)?.value;
}

const millions = (value?: number) => (value == null ? "—" : `${(value / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`);

export default function MarketPage() {
  const [market, setMarket] = useState<MarketData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMarket().then(setMarket).catch(() => setError("Couldn't load market data. Please try again."));
  }, []);

  if (error) {
    return (
      <div className="flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-200 rounded-lg px-4 py-3">
        <AlertCircle className="h-4 w-4 flex-shrink-0" />
        {error}
      </div>
    );
  }
  if (!market) return <p className="text-gray-400 py-16 text-center">Loading…</p>;

  const periods = Array.from(new Set(market.stats.map((s) => s.period))).sort().slice(-RECENT_PERIODS).reverse();
  const largestValue = Math.max(0, ...periods.map((p) => findStat(market.stats, p, BC, "value") ?? 0));
  const largestBucket = Math.max(0, ...market.price_buckets.map((b) => b.count));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <BarChart3 className="h-8 w-8 text-wine-700" />
          Wine Market
        </h1>
        <p className="text-gray-500">Market-wide sales, BC shelf prices and wineries advertised for sale.</p>
      </div>

      <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
        These are market totals. No source used here shows how many bottles any one winery or wine sells, or what it costs to make.
      </p>

      <Card className="p-5 space-y-4">
        <h2 className="text-xl font-semibold text-gray-800">Annual wine sales</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200">
                <th className="py-2 pr-3 font-medium">Year</th>
                <th className="py-2 pr-3 font-medium">BC sales</th>
                <th className="py-2 pr-3 font-medium w-1/4"><span className="sr-only">BC sales bar</span></th>
                <th className="py-2 pr-3 font-medium">BC litres</th>
                <th className="py-2 pr-3 font-medium">BC $ per litre</th>
                <th className="py-2 font-medium">Canada sales</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {periods.map((period) => {
                const value = findStat(market.stats, period, BC, "value");
                const volume = findStat(market.stats, period, BC, "volume");
                return (
                  <tr key={period}>
                    <td className="py-2 pr-3 text-gray-800">{period}</td>
                    <td className="py-2 pr-3">{value != null ? `$${millions(value)}` : "—"}</td>
                    <td className="py-2 pr-3">
                      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                        <div className="h-full bg-wine-600" style={{ width: `${((value ?? 0) / (largestValue || 1)) * 100}%` }} />
                      </div>
                    </td>
                    <td className="py-2 pr-3">{millions(volume)}</td>
                    <td className="py-2 pr-3">{value != null && volume ? formatPrice(value / volume, "CAD") : "—"}</td>
                    <td className="py-2">{`$${millions(findStat(market.stats, period, "Canada", "value"))}`}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-500">
          <SourceLink source={market.stats_source} />. Sales aren&apos;t the same as consumption or consumer spending.
        </p>
      </Card>

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
          Asking prices, entered by hand from public sources, with any reported sale price in the notes. "As of" is the date last checked. Listings change, so confirm details with the listing agent.
        </p>
      </Card>

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

      <Card className="p-5 space-y-2">
        <h2 className="text-xl font-semibold text-gray-800">Further reports</h2>
        <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
          {market.reports.map((report) => (
            <li key={report.label}><SourceLink source={report} /></li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
