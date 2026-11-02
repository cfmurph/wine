"use client";

import { SCORE_LABELS, ScoreName, ScoreWeights } from "@/types/winery";

interface WeightControlsProps {
  weights: ScoreWeights;
  onChange: (weights: ScoreWeights) => void;
}

export function WeightControls({ weights, onChange }: WeightControlsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {(Object.keys(SCORE_LABELS) as ScoreName[]).map((name) => (
        <label key={name} className="block text-sm font-medium text-gray-700">
          <span className="flex justify-between">
            {SCORE_LABELS[name]} weight
            <span className="text-gray-500 font-normal">{weights[name]}</span>
          </span>
          <input
            type="range"
            min={0}
            max={3}
            step={0.5}
            value={weights[name]}
            onChange={(e) => onChange({ ...weights, [name]: Number(e.target.value) })}
            className="w-full accent-wine-700"
          />
        </label>
      ))}
    </div>
  );
}
