"use client";

import { useEffect, useState } from "react";
import { api, DashboardSummary, Prediction, WeatherData, NDWIAnalysis, SprayResult } from "@/lib/api";
import dynamic from "next/dynamic";

const RiskMap = dynamic(() => import("@/components/RiskMap"), { ssr: false });
const ForecastChart = dynamic(() => import("@/components/ForecastChart"), { ssr: false });

function RiskGauge({ score }: { score: number | null }) {
  if (score === null) return <div className="text-4xl font-bold text-slate-600">--</div>;
  const color = score >= 70 ? "text-red-500" : score >= 50 ? "text-orange-500" : score >= 30 ? "text-yellow-500" : "text-emerald-500";
  const label = score >= 70 ? "CRITICAL" : score >= 50 ? "HIGH" : score >= 30 ? "MODERATE" : "LOW";
  return (
    <div className="text-center">
      <div className={`text-5xl font-black ${color}`}>{Math.round(score)}</div>
      <div className={`text-sm font-bold mt-1 ${color}`}>{label}</div>
      <div className="text-xs text-slate-500 mt-1">Risk Score (0-100)</div>
    </div>
  );
}

function KPICard({ label, value, sub, color = "emerald" }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
      <p className={`mt-1 text-2xl font-bold text-${color}-400`}>{value}</p>
      {sub && <p className="text-xs text-slate-600 mt-0.5">{sub}</p>}
    </div>
  );
}

function WeatherWidget({ weather }: { weather: WeatherData | null }) {
  if (!weather || weather.status === "error") {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <h3 className="text-sm font-medium text-slate-400 mb-2">Weather (OpenWeatherMap)</h3>
        <p className="text-xs text-amber-400">API key not configured. Set WEATHER_API_KEY in .env</p>
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <h3 className="text-sm font-medium text-slate-400 mb-3">Live Weather — Sadar Cantt</h3>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-slate-500">Temperature</p>
          <p className="text-xl font-bold text-orange-400">{weather.temperature}C</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Humidity</p>
          <p className="text-xl font-bold text-blue-400">{weather.humidity}%</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Rain (1h)</p>
          <p className="text-xl font-bold text-cyan-400">{weather.rain_1h || 0} mm</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Wind</p>
          <p className="text-xl font-bold text-teal-400">{weather.wind_speed} m/s</p>
        </div>
      </div>
      <p className="text-xs text-slate-600 mt-2">{weather.weather_desc} | {weather.source}</p>
    </div>
  );
}

function NDWIWidget({ ndwi }: { ndwi: NDWIAnalysis | null }) {
  if (!ndwi) return null;
  const a = ndwi.analysis;
  const riskColor = a.breeding_risk === "critical" ? "text-red-500" : a.breeding_risk === "high" ? "text-orange-500" : a.breeding_risk === "moderate" ? "text-yellow-500" : "text-emerald-500";
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <h3 className="text-sm font-medium text-slate-400 mb-3">NDWI Water Analysis (MOSDAC/Sentinel-2)</h3>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-slate-500">Water Class</p>
          <p className="text-sm font-bold text-cyan-400 capitalize">{a.water_class.replace("_", " ")}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">NDWI Mean</p>
          <p className="text-sm font-bold text-blue-400">{a.ndwi_mean}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Stagnant Area</p>
          <p className="text-sm font-bold text-red-400">{(a.stagnant_area_pct * 100).toFixed(1)}%</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Persistence</p>
          <p className="text-sm font-bold text-purple-400">{a.persistence_days} days</p>
        </div>
      </div>
      <div className="mt-3 pt-2 border-t border-slate-800">
        <p className="text-xs text-slate-500">Breeding Risk</p>
        <p className={`text-lg font-black ${riskColor} uppercase`}>{a.breeding_risk}</p>
      </div>
    </div>
  );
}

function SprayWidget({ spray, onOptimize, loading }: { spray: SprayResult | null; onOptimize: () => void; loading: boolean }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-slate-400">Spray Route Optimization (OR-Tools)</h3>
        <button onClick={onOptimize} disabled={loading}
          className="px-3 py-1 text-xs bg-emerald-600 hover:bg-emerald-500 rounded disabled:opacity-50">
          {loading ? "Optimizing..." : "Optimize Routes"}
        </button>
      </div>
      {spray ? (
        <div>
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="text-center">
              <p className="text-lg font-bold text-emerald-400">{spray.total_distance_km} km</p>
              <p className="text-xs text-slate-500">Distance</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-blue-400">{spray.total_fuel_liters} L</p>
              <p className="text-xs text-slate-500">Fuel</p>
            </div>
            <div className="text-center">
              <p className="text-lg font-bold text-yellow-400">Rs {spray.estimated_cost_inr}</p>
              <p className="text-xs text-slate-500">Cost</p>
            </div>
          </div>
          {spray.routes.map((r, i) => (
            <div key={i} className="text-xs text-slate-400 mb-1">
              <span className="font-bold text-emerald-400">{r.vehicle_id}</span>: {r.stops.map(s => s.name).join(" -> ")} ({r.distance_km} km)
            </div>
          ))}
          <p className="text-xs text-slate-600 mt-2">Status: {spray.solver_status} | Vehicles: {spray.vehicles_used} | Time: ~{spray.estimated_time_hours}h</p>
        </div>
      ) : (
        <p className="text-xs text-slate-600">Click optimize to generate fogging routes for Sadar Cantt hotspots</p>
      )}
    </div>
  );
}

function CitizenWidget({ reportSubmitted }: { reportSubmitted: boolean }) {
  const [form, setForm] = useState({ report_type: "mosquito", severity: 3, mosquito_density: 2 });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const res = await api.submitReport({
        ...form,
        latitude: 26.85 + (Math.random() - 0.5) * 0.02,
        longitude: 80.94 + (Math.random() - 0.5) * 0.02,
      });
      setResult(res);
    } catch (e: any) {
      setResult({ error: e.message });
    }
    setSubmitting(false);
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <h3 className="text-sm font-medium text-slate-400 mb-3">Citizen Report (YOLOv11 Analysis)</h3>
      <div className="space-y-2">
        <select value={form.report_type} onChange={e => setForm(f => ({ ...f, report_type: e.target.value }))}
          className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm text-white">
          <option value="mosquito">Mosquito Sighting</option>
          <option value="water_logging">Water Logging</option>
          <option value="drain">Open Drain</option>
          <option value="garbage">Garbage Dump</option>
        </select>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs text-slate-500">Severity (1-5)</label>
            <input type="range" min="1" max="5" value={form.severity}
              onChange={e => setForm(f => ({ ...f, severity: +e.target.value }))}
              className="w-full" />
            <p className="text-center text-xs text-emerald-400">{form.severity}</p>
          </div>
          <div>
            <label className="text-xs text-slate-500">Mosquito Density</label>
            <input type="range" min="1" max="5" value={form.mosquito_density}
              onChange={e => setForm(f => ({ ...f, mosquito_density: +e.target.value }))}
              className="w-full" />
            <p className="text-center text-xs text-orange-400">{form.mosquito_density}</p>
          </div>
        </div>
        <button onClick={handleSubmit} disabled={submitting}
          className="w-full py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm disabled:opacity-50">
          {submitting ? "Submitting..." : "Submit Report"}
        </button>
        {result && (
          <div className={`text-xs p-2 rounded ${result.error ? "bg-red-900/30 text-red-400" : "bg-emerald-900/30 text-emerald-400"}`}>
            {result.error ? result.error : `Report #${result.report_id} submitted. CV analysis: ${result.cv_result?.risk_level || "queued"}`}
          </div>
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [ndwi, setNdwi] = useState<NDWIAnalysis | null>(null);
  const [spray, setSpray] = useState<SprayResult | null>(null);
  const [sprayLoading, setSprayLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const loadData = async () => {
    try {
      const [sum, pred, w, n] = await Promise.allSettled([
        api.getDashboard(),
        api.getPrediction(),
        api.getWeather(),
        api.getNDWI(),
      ]);
      if (sum.status === "fulfilled") setSummary(sum.value);
      if (pred.status === "fulfilled") setPrediction(pred.value);
      if (w.status === "fulfilled") setWeather(w.value);
      if (n.status === "fulfilled") setNdwi(n.value);
      setLastRefresh(new Date());
      setError(null);
    } catch (e: any) {
      setError(e.message);
    }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);
  useEffect(() => {
    const interval = setInterval(loadData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleOptimize = async () => {
    setSprayLoading(true);
    try {
      const result = await api.optimizeSpray(2);
      setSpray(result);
    } catch (e: any) {
      console.error(e);
    }
    setSprayLoading(false);
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🦟</div>
          <p className="text-emerald-400 text-lg font-medium">Loading MosquiSense AI...</p>
          <p className="text-slate-500 text-sm mt-2">Fetching Sadar Cantt data</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <header className="mb-6 border-b border-slate-800 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm uppercase tracking-widest text-emerald-400">Lucknow Municipal Corporation</p>
            <h1 className="text-3xl font-bold text-white">MosquiSense AI Dashboard</h1>
            <p className="mt-1 text-slate-400">Sadar Cantt Ward (SC-001) | 15-day outbreak prediction | Real-time MOSDAC satellite data</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-500">Last refresh</p>
            <p className="text-xs text-slate-400">{lastRefresh.toLocaleTimeString()}</p>
            <p className="text-xs text-slate-600 mt-1">Auto-refresh: 60s</p>
          </div>
        </div>
      </header>

      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded text-red-400 text-sm">
          API Error: {error} — Make sure backend is running on port 8000
        </div>
      )}

      {/* KPI Cards */}
      <section className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <KPICard label="Risk Index" value={summary?.kpi.risk_score !== null && summary?.kpi.risk_score !== undefined ? Math.round(summary.kpi.risk_score) : "--"} sub="0-100 scale" color={summary && summary.kpi.risk_score && summary.kpi.risk_score > 50 ? "red" : "emerald"} />
        <KPICard label="Outbreak Prob" value={summary?.kpi.outbreak_probability !== null && summary?.kpi.outbreak_probability !== undefined ? `${(summary.kpi.outbreak_probability * 100).toFixed(1)}%` : "--"} sub="15-day forecast" color="yellow" />
        <KPICard label="Active Hotspots" value={summary?.kpi.active_hotspots || 0} sub="Sadar Cantt area" color="orange" />
        <KPICard label="Citizen Reports" value={summary?.kpi.citizen_reports_total || 0} sub={`${summary?.kpi.mosquito_reports || 0} mosquito`} color="blue" />
        <KPICard label="Predictions" value={summary?.kpi.predictions_run || 0} sub="Historical runs" color="purple" />
        <KPICard label="Model" value="v1.0" sub={summary?.kpi.model_version || "ensemble"} color="teal" />
      </section>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column — Map + Weather */}
        <div className="lg:col-span-2 space-y-6">
          <RiskMap />
          <WeatherWidget weather={weather} />
          <ForecastChart prediction={prediction} />
        </div>

        {/* Right Column — NDWI, Spray, Citizen */}
        <div className="space-y-6">
          <NDWIWidget ndwi={ndwi} />
          <SprayWidget spray={spray} onOptimize={handleOptimize} loading={sprayLoading} />
          <CitizenWidget reportSubmitted={false} />
        </div>
      </div>

      {/* Model Breakdown */}
      {prediction && (
        <section className="mt-6 rounded-lg border border-slate-800 bg-slate-900 p-4">
          <h3 className="text-sm font-medium text-slate-400 mb-3">Ensemble Model Breakdown</h3>
          <div className="grid grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-slate-500">CatBoost (40%)</p>
              <p className="text-lg font-bold text-emerald-400">{(prediction.model_breakdown.catboost_probability * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">TFT 15-day (35%)</p>
              <p className="text-lg font-bold text-blue-400">{(prediction.model_breakdown.tft_probability_15d * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">NDWI Signal (25%)</p>
              <p className="text-lg font-bold text-cyan-400">{(prediction.model_breakdown.ndwi_signal * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Ensemble Output</p>
              <p className="text-lg font-bold text-yellow-400">{(prediction.outbreak_probability * 100).toFixed(1)}%</p>
            </div>
          </div>
          <div className="mt-3">
            <p className="text-xs text-slate-500 mb-1">Top Feature Drivers</p>
            <div className="flex gap-2 flex-wrap">
              {prediction.top_drivers.map((d, i) => (
                <span key={i} className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-300">
                  {d.feature}: {(d.impact * 100).toFixed(0)}%
                </span>
              ))}
            </div>
          </div>
        </section>
      )}
    </main>
  );
}
