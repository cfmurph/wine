import { formatPrice } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { AnalysisCheck, CheckLine, DealFinancials } from "@/types/deal";

const STATUS: Record<AnalysisCheck["status"], string> = {
  computed: "Calculated",
  review: "Needs review",
  unknown: "Unknown",
};

function formatLine(line: CheckLine) {
  if (line.value == null) return "Unknown";
  if (line.unit === "currency") return formatPrice(line.value, "CAD");
  if (line.unit === "percent") return `${(line.value * 100).toFixed(1)}%`;
  if (line.unit === "multiple") return `${line.value.toFixed(2)}x`;
  return line.value.toLocaleString(undefined, { maximumFractionDigits: 1 });
}

export function ScreeningChecks({ data }: { data: DealFinancials }) {
  return (
    <Card className="p-5 space-y-4">
      <h2 className="text-xl font-semibold text-gray-800">
        Screening checks{data.analysis_year ? ` (${data.analysis_year})` : ""}
      </h2>
      <div className="grid gap-4 lg:grid-cols-2">
        {data.checks.map((check) => (
          <div key={check.title} className="border border-gray-100 rounded-lg p-4 space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="font-medium text-gray-800">{check.title}</h3>
              <Badge variant={check.status === "review" ? "wine" : check.status === "unknown" ? "outline" : "default"}>{STATUS[check.status]}</Badge>
            </div>
            <p className="text-sm text-gray-600">{check.note}</p>
            <dl className="text-sm space-y-1">
              {check.lines.map((line) => (
                <div key={line.label} className="flex justify-between gap-3">
                  <dt className="text-gray-500">{line.label}</dt>
                  <dd className={line.value == null ? "text-gray-400" : "font-medium text-gray-800"}>{formatLine(line)}</dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>
    </Card>
  );
}
