"use client";

import { Prediction } from "@/lib/api";

export default function ForecastChart({ prediction }: { prediction: Prediction | null }) {
  if (!prediction || !prediction.horizon_15d || prediction.horizon_15d.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
        <h2 className="mb-4 text-lg font-medium text-slate-400">15-Day Outbreak Forecast</h2>
        <div className="flex h-64 items-center justify-center rounded border border-dashed border-slate-700 text-slate-500 text-sm">
          Run prediction to see 15-day forecast chart
        </div>
      </div>
    );
  }

  const horizon = prediction.horizon_15d;
  const maxProb = Math.max(...horizon.map(h => h.probability), 0.6);

  // Chart dimensions
  const chartWidth = 600;
  const chartHeight = 240;
  const padding = { top: 20, right: 20, bottom: 40, left: 50 };
  const plotWidth = chartWidth - padding.left - padding.right;
  const plotHeight = chartHeight - padding.top - padding.bottom;

  // Generate SVG path for probability line
  const points = horizon.map((h, i) => ({
    x: padding.left + (i / (horizon.length - 1)) * plotWidth,
    y: padding.top + plotHeight - (h.probability / maxProb) * plotHeight,
  }));

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  // Area fill path
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${padding.top + plotHeight} L ${points[0].x} ${padding.top + plotHeight} Z`;

  // Danger threshold line (0.6 = 60%)
  const dangerY = padding.top + plotHeight - (0.6 / maxProb) * plotHeight;

  // Risk color for the current day
  const currentProb = horizon[0]?.probability || 0;
  const riskColor = currentProb >= 0.6 ? "#ef4444" : currentProb >= 0.4 ? "#f97316" : currentProb >= 0.2 ? "#eab308" : "#10b981";

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium text-slate-400">15-Day Outbreak Forecast</h2>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-red-500"></span> Danger (60%)</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full" style={{ backgroundColor: riskColor }}></span> Today: {(currentProb * 100).toFixed(1)}%</span>
        </div>
      </div>

      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full">
        {/* Grid lines */}
        {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map(v => {
          if (v > maxProb * 1.2) return null;
          const y = padding.top + plotHeight - (v / maxProb) * plotHeight;
          return (
            <g key={v}>
              <line x1={padding.left} y1={y} x2={padding.left + plotWidth} y2={y} stroke="#334155" strokeWidth={0.5} />
              <text x={padding.left - 8} y={y + 3} textAnchor="end" fill="#64748b" fontSize={9}>
                {(v * 100).toFixed(0)}%
              </text>
            </g>
          );
        })}

        {/* Day labels */}
        {horizon.map((h, i) => {
          const x = padding.left + (i / (horizon.length - 1)) * plotWidth;
          return (
            <text key={i} x={x} y={chartHeight - 8} textAnchor="middle" fill="#64748b" fontSize={9}>
              D+{h.day}
            </text>
          );
        })}

        {/* Danger threshold line */}
        <line x1={padding.left} y1={dangerY} x2={padding.left + plotWidth} y2={dangerY}
          stroke="#ef4444" strokeWidth={1} strokeDasharray="6" opacity={0.5} />
        <text x={padding.left + plotWidth + 4} y={dangerY + 3} fill="#ef4444" fontSize={8} opacity={0.7}>60%</text>

        {/* Area fill */}
        <path d={areaPath} fill="url(#areaGradient)" opacity={0.3} />

        {/* Gradient definition */}
        <defs>
          <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={riskColor} stopOpacity={0.4} />
            <stop offset="100%" stopColor={riskColor} stopOpacity={0.05} />
          </linearGradient>
        </defs>

        {/* Probability line */}
        <path d={linePath} fill="none" stroke={riskColor} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />

        {/* Data points */}
        {points.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={3} fill={riskColor} stroke="#0f172a" strokeWidth={1.5} />
        ))}

        {/* Current day highlight */}
        <circle cx={points[0]?.x} cy={points[0]?.y} r={6} fill={riskColor} stroke="#0f172a" strokeWidth={2} />
        <text x={points[0]?.x} y={(points[0]?.y || 0) - 12} textAnchor="middle" fill={riskColor} fontSize={10} fontWeight="bold">
          {(currentProb * 100).toFixed(1)}%
        </text>
      </svg>

      <div className="mt-3 flex justify-between text-xs text-slate-500">
        <span>Model: {prediction.model_version}</span>
        <span>Risk: {prediction.breeding_risk.toUpperCase()}</span>
      </div>
    </div>
  );
}
