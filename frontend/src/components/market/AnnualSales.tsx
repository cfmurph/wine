import { formatPrice } from "@/lib/utils";
import { Card } from "@/components/ui/Card";
import { SourceLink } from "@/components/market/SourceLink";
import { MarketData, MarketStat } from "@/types/winery";

const RECENT_PERIODS = 10;
const BC = "British Columbia";

function findStat(stats: MarketStat[], period: string, geography: string, metric: MarketStat["metric"]) {
  return stats.find((s) => s.period === period && s.geography === geography && s.metric === metric)?.value;
}

const millions = (value?: number) => (value == null ? "—" : `${(value / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`);

export function AnnualSales({ market }: { market: MarketData }) {
  const periods = Array.from(new Set(market.stats.map((s) => s.period))).sort().slice(-RECENT_PERIODS).reverse();
  const largestValue = Math.max(0, ...periods.map((p) => findStat(market.stats, p, BC, "value") ?? 0));

  return (
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
  );
}
