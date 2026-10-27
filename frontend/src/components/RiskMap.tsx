"use client";

import { useEffect, useState } from "react";
import { api, Hotspot } from "@/lib/api";

const HOTSPOTS: Hotspot[] = [
  { id: "H1", name: "Sadar Bazaar", lat: 26.845, lon: 80.935, risk_weight: 1.2 },
  { id: "H2", name: "Nehru Road", lat: 26.848, lon: 80.940, risk_weight: 1.0 },
  { id: "H3", name: "Cantonment Board", lat: 26.852, lon: 80.943, risk_weight: 0.8 },
  { id: "H4", name: "Kanpur Road", lat: 26.840, lon: 80.938, risk_weight: 1.1 },
  { id: "H5", name: "Hazratganj Border", lat: 26.855, lon: 80.948, risk_weight: 0.9 },
  { id: "H6", name: "Alambagh Crossing", lat: 26.835, lon: 80.930, risk_weight: 1.3 },
  { id: "H7", name: "Charbagh Area", lat: 26.850, lon: 80.928, risk_weight: 0.7 },
  { id: "H8", name: "Aminabad Market", lat: 26.858, lon: 80.942, risk_weight: 1.0 },
];

const DEPOT = { lat: 26.850, lon: 80.940, name: "Sadar Cantt Depot" };

// Sadar Cantt approximate boundary polygon
const WARD_BOUNDARY = [
  [26.830, 80.920], [26.830, 80.960], [26.870, 80.960], [26.870, 80.920], [26.830, 80.920],
];

export default function RiskMap() {
  const [selectedHotspot, setSelectedHotspot] = useState<Hotspot | null>(null);

  // Calculate pixel positions from lat/lon
  const mapBounds = { south: 26.825, north: 26.865, west: 80.915, east: 80.965 };
  const mapWidth = 700;
  const mapHeight = 400;

  const toPixel = (lat: number, lon: number) => ({
    x: ((lon - mapBounds.west) / (mapBounds.east - mapBounds.west)) * mapWidth,
    y: ((mapBounds.north - lat) / (mapBounds.north - mapBounds.south)) * mapHeight,
  });

  const depotPx = toPixel(DEPOT.lat, DEPOT.lon);
  const boundaryPixels = WARD_BOUNDARY.map(([lat, lon]) => toPixel(lat, lon));

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-slate-400">Risk Heatmap — Sadar Cantt, Lucknow</h3>
        <div className="flex gap-3 text-xs">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"></span> Critical</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500"></span> High</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500"></span> Medium</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> Low</span>
        </div>
      </div>

      <div className="relative bg-slate-950 rounded border border-slate-800 overflow-hidden" style={{ height: 400 }}>
        <svg viewBox={`0 0 ${mapWidth} ${mapHeight}`} className="w-full h-full">
          {/* Grid lines */}
          {Array.from({ length: 5 }).map((_, i) => {
            const y = (i / 4) * mapHeight;
            const lat = mapBounds.north - (i / 4) * (mapBounds.north - mapBounds.south);
            return (
              <g key={`grid-${i}`}>
                <line x1={0} y1={y} x2={mapWidth} y2={y} stroke="#334155" strokeWidth={0.5} strokeDasharray="4" />
                <text x={4} y={y - 4} fill="#64748b" fontSize={9}>{lat.toFixed(2)}</text>
              </g>
            );
          })}
          {Array.from({ length: 5 }).map((_, i) => {
            const x = (i / 4) * mapWidth;
            const lon = mapBounds.west + (i / 4) * (mapBounds.east - mapBounds.west);
            return (
              <g key={`gridx-${i}`}>
                <line x1={x} y1={0} x2={x} y2={mapHeight} stroke="#334155" strokeWidth={0.5} strokeDasharray="4" />
                <text x={x + 4} y={mapHeight - 4} fill="#64748b" fontSize={9}>{lon.toFixed(2)}</text>
              </g>
            );
          })}

          {/* Ward boundary */}
          <polygon
            points={boundaryPixels.map(p => `${p.x},${p.y}`).join(" ")}
            fill="rgba(16, 185, 129, 0.05)"
            stroke="#10b981"
            strokeWidth={1.5}
            strokeDasharray="6"
          />
          <text x={boundaryPixels[0].x + 8} y={boundaryPixels[0].y + 14} fill="#10b981" fontSize={10} fontWeight="bold">
            Ward SC-001 Boundary
          </text>

          {/* Risk zones (circles with opacity based on risk) */}
          {HOTSPOTS.map(h => {
            const px = toPixel(h.lat, h.lon);
            const radius = 20 + h.risk_weight * 15;
            const color = h.risk_weight > 1.1 ? "rgba(239,68,68,0.2)" : h.risk_weight > 0.9 ? "rgba(249,115,22,0.2)" : "rgba(234,179,8,0.15)";
            return (
              <circle key={h.id} cx={px.x} cy={px.y} r={radius} fill={color} stroke="none" />
            );
          })}

          {/* Hotspot markers */}
          {HOTSPOTS.map(h => {
            const px = toPixel(h.lat, h.lon);
            const fillColor = h.risk_weight > 1.1 ? "#ef4444" : h.risk_weight > 0.9 ? "#f97316" : "#eab308";
            return (
              <g key={h.id} onClick={() => setSelectedHotspot(h)} style={{ cursor: "pointer" }}>
                <circle cx={px.x} cy={px.y} r={8} fill={fillColor} stroke="#0f172a" strokeWidth={2} />
                <text x={px.x} y={px.y + 3} textAnchor="middle" fill="white" fontSize={8} fontWeight="bold">
                  {h.id.replace("H", "")}
                </text>
                <text x={px.x} y={px.y + 18} textAnchor="middle" fill="#94a3b8" fontSize={8}>
                  {h.name}
                </text>
              </g>
            );
          })}

          {/* Depot marker */}
          <g>
            <rect x={depotPx.x - 6} y={depotPx.y - 6} width={12} height={12} fill="#3b82f6" stroke="#0f172a" strokeWidth={2} rx={2} />
            <text x={depotPx.x} y={depotPx.y + 3} textAnchor="middle" fill="white" fontSize={7} fontWeight="bold">D</text>
            <text x={depotPx.x} y={depotPx.y + 20} textAnchor="middle" fill="#3b82f6" fontSize={8} fontWeight="bold">{DEPOT.name}</text>
          </g>

          {/* Coordinates label */}
          <text x={mapWidth - 8} y={14} textAnchor="end" fill="#475569" fontSize={9}>
            26.85N, 80.94E | EPSG:4326
          </text>
        </svg>
      </div>

      {selectedHotspot && (
        <div className="mt-3 p-3 bg-slate-800/50 rounded text-xs">
          <span className="font-bold text-white">{selectedHotspot.name}</span>
          <span className="text-slate-400 ml-2">({selectedHotspot.lat}, {selectedHotspot.lon})</span>
          <span className="text-slate-500 ml-2">Risk weight: {selectedHotspot.risk_weight}</span>
          <button onClick={() => setSelectedHotspot(null)} className="ml-2 text-slate-500 hover:text-white">x</button>
        </div>
      )}
    </div>
  );
}
