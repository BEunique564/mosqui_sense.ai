"use client";

/**
 * Municipality Dashboard — Module 11
 * Government-grade overview for Lucknow Municipal Corporation officers.
 */

const KPI_CARDS = [
  { label: "City Risk Index", value: "—", sub: "0–100 scale" },
  { label: "15-Day Forecast", value: "—", sub: "Highest ward probability" },
  { label: "Active Hotspots", value: "—", sub: "ST-DBSCAN clusters" },
  { label: "Fuel Saved (MTD)", value: "—", sub: "vs reactive baseline" },
  { label: "Complaints (7d)", value: "—", sub: "Citizen + municipal" },
  { label: "Model Version", value: "ensemble-v0", sub: "CatBoost + TFT + NDWI" },
];

export default function DashboardPage() {
  return (
    <main className="min-h-screen p-6">
      <header className="mb-8 border-b border-slate-800 pb-4">
        <p className="text-sm uppercase tracking-widest text-emerald-400">
          Lucknow Municipal Corporation
        </p>
        <h1 className="text-3xl font-semibold text-white">MosquiSense AI Dashboard</h1>
        <p className="mt-1 text-slate-400">
          15-day outbreak prediction · Spray optimization · Citizen alerts
        </p>
      </header>

      <section className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {KPI_CARDS.map((card) => (
          <div
            key={card.label}
            className="rounded-lg border border-slate-800 bg-slate-900 p-4"
          >
            <p className="text-xs text-slate-500">{card.label}</p>
            <p className="mt-1 text-2xl font-bold text-emerald-400">{card.value}</p>
            <p className="text-xs text-slate-600">{card.sub}</p>
          </div>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 text-lg font-medium">Risk Heatmap</h2>
          <div className="flex h-64 items-center justify-center rounded border border-dashed border-slate-700 text-slate-500">
            Leaflet + GeoServer WMS — connect API /gis/tiles
          </div>
        </div>
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
          <h2 className="mb-4 text-lg font-medium">15-Day Outbreak Forecast</h2>
          <div className="flex h-64 items-center justify-center rounded border border-dashed border-slate-700 text-slate-500">
            Chart.js — /v1/predictions/wards
          </div>
        </div>
      </section>
    </main>
  );
}
