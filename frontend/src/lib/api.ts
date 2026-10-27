const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  return res.json();
}

export interface DashboardSummary {
  location: string;
  ward: { code: string; name: string; population: number; center: { lat: number; lon: number } };
  kpi: {
    risk_score: number | null;
    outbreak_probability: number | null;
    breeding_risk: string;
    active_hotspots: number;
    citizen_reports_total: number;
    mosquito_reports: number;
    waterlogging_reports: number;
    model_version: string;
    predictions_run: number;
  };
  weather: any;
  ndwi: { water_class: string; stagnant_area_pct: number; breeding_risk: string; persistence_days: number };
  satellite_status: any;
  timestamp: string;
}

export interface Prediction {
  ward_code: string;
  ward_name: string;
  risk_score: number;
  outbreak_probability: number;
  breeding_risk: string;
  horizon_15d: { day: number; probability: number }[];
  model_version: string;
  top_drivers: { feature: string; impact: number }[];
  model_breakdown: any;
  features_used: any;
  timestamp: string;
}

export interface WeatherData {
  status: string;
  source?: string;
  temperature?: number;
  humidity?: number;
  rainfall_mm?: number;
  wind_speed?: number;
  weather_main?: string;
  weather_desc?: string;
  timestamp?: string;
}

export interface NDWIAnalysis {
  ward_code: string;
  ward_name: string;
  analysis: {
    ndwi_mean: number;
    water_class: string;
    persistence_days: number;
    stagnant_area_pct: number;
    water_persistence_index: number;
    breeding_risk: string;
  };
  history_count: number;
  latest_records: any[];
}

export interface Hotspot {
  id: string;
  name: string;
  lat: number;
  lon: number;
  risk_weight: number;
}

export interface SprayRoute {
  vehicle_id: string;
  stops: { hotspot_id: string; name: string; lat: number; lon: number }[];
  distance_km: number;
}

export interface SprayResult {
  routes: SprayRoute[];
  total_fuel_liters: number;
  estimated_cost_inr: number;
  solver_status: string;
  total_distance_km: number;
  estimated_time_hours: number;
  vehicles_used: number;
}

export interface CitizenReport {
  id: number;
  report_type: string;
  latitude: number;
  longitude: number;
  severity: number;
  status: string;
  created_at: string;
}

// API functions
export const api = {
  getHealth: () => fetchAPI<any>("/health"),
  getDashboard: () => fetchAPI<DashboardSummary>("/v1/dashboard/summary"),
  getPrediction: () => fetchAPI<Prediction>("/v1/predictions/wards/sadar-cantt"),
  getPredictionHistory: (limit = 30) => fetchAPI<any>(`/v1/predictions/history?limit=${limit}`),
  triggerPrediction: () => fetchAPI<Prediction>("/v1/predictions/trigger", { method: "POST" }),

  getWeather: () => fetchAPI<WeatherData>("/v1/weather/current"),
  getWeatherForecast: () => fetchAPI<any>("/v1/weather/forecast"),
  getWeatherHistory: (days = 30) => fetchAPI<any>(`/v1/weather/history?days=${days}`),

  getNDWI: () => fetchAPI<NDWIAnalysis>("/v1/satellite/ndwi"),
  getSatelliteHistory: (days = 30) => fetchAPI<any>(`/v1/satellite/history?days=${days}`),
  getSatelliteStatus: () => fetchAPI<any>("/v1/satellite/status"),

  getHotspots: () => fetchAPI<{ hotspots: Hotspot[]; depot: any }>("/v1/spray/hotspots"),
  optimizeSpray: (vehicleCount = 2) =>
    fetchAPI<SprayResult>(`/v1/spray/optimize?vehicle_count=${vehicleCount}`, { method: "POST" }),

  submitReport: (data: {
    report_type: string;
    latitude: number;
    longitude: number;
    severity: number;
    mosquito_density?: number;
  }) => {
    const params = new URLSearchParams(data as any);
    return fetchAPI<any>(`/v1/citizen/reports?${params}`, { method: "POST" });
  },
  getReports: (limit = 20) => fetchAPI<any>(`/v1/citizen/reports?limit=${limit}`),

  getWard: () => fetchAPI<any>("/v1/wards/sadar-cantt"),
};
