"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function SatelliteStatusPanel() {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSatelliteStatus().then(res => {
      setStatus(res);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-slate-500 text-xs p-2">Loading satellite status...</div>;
  if (!status) return null;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <h3 className="text-sm font-medium text-slate-400 mb-3">MOSDAC Satellite Status (ISRO)</h3>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-slate-500">MOSDAC API</span>
          <span className={status.mosdac_api_available ? "text-emerald-400" : "text-red-400"}>
            {status.mosdac_api_available ? "Online" : "Offline"}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-500">Credentials</span>
          <span className={status.credentials_configured ? "text-emerald-400" : "text-amber-400"}>
            {status.credentials_configured ? "Configured" : "Not Set"}
          </span>
        </div>

        <div className="pt-2 border-t border-slate-800">
          <p className="text-slate-500 mb-1">Available Datasets:</p>
          {Object.entries(status.available_datasets || {}).map(([key, desc]) => (
            <div key={key} className="ml-2 text-slate-400">
              <span className="font-mono text-cyan-400">{key}</span>
              <span className="text-slate-600 ml-1">— {String(desc).substring(0, 40)}...</span>
            </div>
          ))}
        </div>

        <div className="pt-2 border-t border-slate-800">
          <p className="text-slate-500 mb-1">Bounding Box (Sadar Cantt):</p>
          <p className="font-mono text-slate-400 ml-2">
            {status.bounding_box?.south}N to {status.bounding_box?.north}N, {status.bounding_box?.west}E to {status.bounding_box?.east}E
          </p>
        </div>

        <div className="pt-2 border-t border-slate-800 space-y-1">
          {!status.credentials_configured && (
            <p className="text-amber-400">
              1. Register at <a href="https://mosdac.gov.in/signup/" target="_blank" className="underline">mosdac.gov.in/signup/</a>
            </p>
          )}
          {!status.credentials_configured && (
            <p className="text-amber-400">2. Set MOSDAC_USERNAME + MOSDAC_PASSWORD in .env</p>
          )}
          <p className="text-slate-500">
            API Manual: <a href="https://mosdac.gov.in/downloadapi-manual" target="_blank" className="underline text-blue-400">mosdac.gov.in/downloadapi-manual</a>
          </p>
        </div>
      </div>
    </div>
  );
}
