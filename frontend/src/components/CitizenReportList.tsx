"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function CitizenReportList() {
  const [reports, setReports] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getReports(10).then(res => {
      setReports(res.reports || []);
      setStats(res.stats || null);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const typeIcon: Record<string, string> = {
    mosquito: "🦟",
    water_logging: "💧",
    drain: "🚰",
    garbage: "🗑️",
  };

  const severityColor = (s: number) => {
    if (s >= 4) return "text-red-400";
    if (s >= 3) return "text-orange-400";
    if (s >= 2) return "text-yellow-400";
    return "text-emerald-400";
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <h3 className="text-sm font-medium text-slate-400 mb-3">Citizen Reports — Sadar Cantt</h3>

      {stats && (
        <div className="grid grid-cols-4 gap-2 mb-3 text-center">
          <div>
            <p className="text-lg font-bold text-blue-400">{stats.total_reports || 0}</p>
            <p className="text-xs text-slate-500">Total</p>
          </div>
          <div>
            <p className="text-lg font-bold text-orange-400">{stats.mosquito_reports || 0}</p>
            <p className="text-xs text-slate-500">Mosquito</p>
          </div>
          <div>
            <p className="text-lg font-bold text-cyan-400">{stats.waterlogging_reports || 0}</p>
            <p className="text-xs text-slate-500">Water</p>
          </div>
          <div>
            <p className="text-lg font-bold text-yellow-400">{stats.avg_severity ? Number(stats.avg_severity).toFixed(1) : "--"}</p>
            <p className="text-xs text-slate-500">Avg Severity</p>
          </div>
        </div>
      )}

      {loading ? (
        <p className="text-xs text-slate-500">Loading...</p>
      ) : reports.length === 0 ? (
        <p className="text-xs text-slate-600">No reports yet. Submit one above.</p>
      ) : (
        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {reports.map(r => (
            <div key={r.id} className="flex items-center gap-2 text-xs p-1.5 bg-slate-800/50 rounded">
              <span>{typeIcon[r.report_type] || "?"}</span>
              <span className="text-slate-300 capitalize">{r.report_type.replace("_", " ")}</span>
              <span className={severityColor(r.severity)}>Sev {r.severity}</span>
              <span className="text-slate-600 ml-auto">{new Date(r.created_at).toLocaleDateString()}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
