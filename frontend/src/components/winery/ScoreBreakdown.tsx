import { SCORE_LABELS, ScoreName, WinerySummary } from "@/types/winery";

export function formatWineryScore(score?: number | null) {
  return score == null ? "Unknown" : Math.round(score).toString();
}

/** How many of a winery's scoring inputs have data, e.g. "4/9 data points". */
export function dataCoverage(winery: WinerySummary) {
  const scores = Object.values(winery.sub_scores);
  const available = scores.reduce((sum, s) => sum + s.available, 0);
  const total = scores.reduce((sum, s) => sum + s.total, 0);
  return `${available}/${total} data points`;
}

export function ScoreBar({ score }: { score?: number | null }) {
  return (
    <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
      {score != null && <div className="h-full bg-wine-600" style={{ width: `${score}%` }} />}
    </div>
  );
}

export function ScoreBreakdown({ winery }: { winery: WinerySummary }) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {(Object.keys(SCORE_LABELS) as ScoreName[]).map((name) => {
        const subScore = winery.sub_scores[name];
        return (
          <div key={name} className="space-y-3">
            <div className="flex items-baseline justify-between">
              <h3 className="font-semibold text-gray-800">{SCORE_LABELS[name]}</h3>
              <span className="text-sm text-gray-500">
                <strong className="text-gray-900">{formatWineryScore(subScore.score)}</strong>
                {" · "}
                {subScore.available}/{subScore.total} data points
              </span>
            </div>
            {subScore.components.map((component) => (
              <div key={component.label} className="text-sm space-y-1">
                <div className="flex justify-between text-gray-700">
                  <span>{component.label}</span>
                  <span>{formatWineryScore(component.score)}</span>
                </div>
                <ScoreBar score={component.score} />
                <p className="text-xs text-gray-500">{component.detail}</p>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}

export function ScreeningNotice() {
  return (
    <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
      Scores are a screening aid, not an appraisal. They use public data only, leave out anything
      unknown, and need data in at least two of the four areas. They don&apos;t reflect any
      winery&apos;s actual sales or costs. Those have to come from the seller during due diligence.
    </p>
  );
}
