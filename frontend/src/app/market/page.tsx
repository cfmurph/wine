"use client";

import { BarChart3 } from "lucide-react";
import { AnnualSales } from "@/components/market/AnnualSales";
import { ListingsTable } from "@/components/market/ListingsTable";
import { RecheckList } from "@/components/market/RecheckList";
import { SalesTable } from "@/components/market/SalesTable";
import { ShelfPrices } from "@/components/market/ShelfPrices";
import { SourceLink } from "@/components/market/SourceLink";
import { Card } from "@/components/ui/Card";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { useFetch } from "@/hooks/useFetch";
import { getMarket } from "@/lib/api";

export default function MarketPage() {
  const { data: market, failed } = useFetch("market", getMarket);

  if (failed) return <ErrorMessage>Couldn&apos;t load market data. Please try again.</ErrorMessage>;
  if (!market) return <p className="text-gray-400 py-16 text-center">Loading…</p>;

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

      <AnnualSales market={market} />
      <ShelfPrices market={market} />
      <ListingsTable market={market} />
      <RecheckList market={market} />
      <SalesTable market={market} />

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
