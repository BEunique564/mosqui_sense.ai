"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function WeatherHistoryChart() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getWeatherHistory(14).then(res => {
      setData(res.data || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-slate-500 text-sm p-4">Loading weather history...</div>;
  if (!data.length) return <div className="text-slate-500 text-sm p-4">No weather history available</div>;

  const chartWidth = 600;
  const chartHeight = 180;
  const padding = { top: 15, right: 15, bottom: 30, left: 45 };
  const plotWidth = chartWidth - padding.left - padding.right;
  const plotHeight = chartHeight - padding.top - padding.bottom;

  const temps = data.map(d => d.temperature).filter(Boolean);
  const rains = data.map(d => d.rainfall_mm).filter(Boolean);
  const maxTemp = Math.max(...temps, 45);
  const maxRain = Math.max(...rains, 30);

  const tempPoints = temps.map((t, i) => ({
    x: padding.left + (i / (temps.length - 1)) * plotWidth,
    y: padding.top + plotHeight - (t / maxTemp) * plotHeight,
  }));

  const rainPoints = rains.map((r, i) => ({
    x: padding.left + (i / (rains.length - 1)) * plotWidth,
    y: padding.top + plotHeight - (r / maxRain) * plotHeight,
  }));

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <h3 className="text-sm font-medium text-slate-400 mb-3">14-Day Weather History — Sadar Cantt</h3>
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full">
        {/* Grid */}
        {[0, 0.25, 0.5, 0.75, 1].map(v => {
          const y = padding.top + plotHeight - v * plotHeight;
          return <line key={v} x1={padding.left} y1={y} x2={padding.left + plotWidth} y2={y} stroke="#334155" strokeWidth={0.5} />;
        })}

        {/* Rainfall bars */}
        {rainPoints.map((p, i) => (
          <rect key={`r${i}`} x={p.x - 4} y={p.y} width={8} height={padding.top + plotHeight - p.y}
            fill="rgba(6,182,212,0.4)" rx={1} />
        ))}

        {/* Temperature line */}
        <path d={tempPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ")}
          fill="none" stroke="#f97316" strokeWidth={2} />
        {tempPoints.map((p, i) => (
          <circle key={`t${i}`} cx={p.x} cy={p.y} r={2.5} fill="#f97316" />
        ))}
      </svg>
      <div className="flex gap-4 mt-2 text-xs">
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-orange-500"></span> Temperature (C)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-2 bg-cyan-500/40 rounded"></span> Rainfall (mm)</span>
      </div>
    </div>
  );
}
