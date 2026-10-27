"""
Feature Engineering Engine — Computes ward-level features for prediction.

Adapted from training/feature_engineering/build_features.py to work
with real SQLite data from weather + satellite sources.
"""

import numpy as np
from datetime import datetime, timezone
from typing import Optional


def rolling_sum(values: list[float], window: int) -> float:
    if not values:
        return 0.0
    return sum(values[-window:])


def rolling_mean(values: list[float], window: int) -> float:
    if not values:
        return 0.0
    subset = values[-window:]
    return sum(subset) / len(subset)


def compute_slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values))
    slope, _ = np.polyfit(x, values, 1)
    return float(slope)


def build_ward_features(
    weather_history: list[dict],
    satellite_history: list[dict],
    ward_info: dict,
    reference_date: Optional[datetime] = None,
) -> dict:
    """Build single-row feature dict for CatBoost / ensemble prediction.

    Uses real historical data from SQLite database.
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)

    # Extract time series
    temps = [w["temperature"] for w in weather_history if w.get("temperature") is not None]
    humidities = [w["humidity"] for w in weather_history if w.get("humidity") is not None]
    rainfalls = [w["rainfall_mm"] for w in weather_history if w.get("rainfall_mm") is not None]
    wind_speeds = [w.get("wind_speed", 0) for w in weather_history]

    ndwi_values = [s["ndwi_mean"] for s in satellite_history if s.get("ndwi_mean") is not None]
    lst_values = [s["lst"] for s in satellite_history if s.get("lst") is not None]
    ndvi_values = [s["ndvi_mean"] for s in satellite_history if s.get("ndvi_mean") is not None]
    stagnant_pcts = [s.get("ndwi_stagnant_pct", 0) for s in satellite_history]
    wpi_values = [s.get("water_persistence_index", 0) for s in satellite_history]

    # Rainfall features
    rain_7d = rolling_sum(rainfalls, 7)
    rain_15d = rolling_sum(rainfalls, 15)

    # Humidity trend (7-day slope)
    humidity_trend = compute_slope(humidities[-7:]) if len(humidities) >= 2 else 0.0

    # Temperature anomaly (deviation from 30-day mean)
    temp_mean_30d = rolling_mean(temps, 30) if temps else 28.0
    temp_anomaly = (temps[-1] - temp_mean_30d) if temps else 0.0

    # NDWI features
    ndwi_change = 0.0
    if len(ndwi_values) >= 2:
        ndwi_change = ndwi_values[-1] - ndwi_values[-7] if len(ndwi_values) >= 7 else ndwi_values[-1] - ndwi_values[0]

    lst_diff = 0.0
    if len(lst_values) >= 2:
        lst_diff = lst_values[-1] - lst_values[-7] if len(lst_values) >= 7 else lst_values[-1] - lst_values[0]

    # Water features
    ndwi_stagnant_pct = stagnant_pcts[-1] if stagnant_pcts else 0.0
    water_persistence = wpi_values[-1] if wpi_values else 0.0
    ndvi_mean = ndvi_values[-1] if ndvi_values else 0.3

    # Complaint density (placeholder — would come from citizen reports)
    ward_area = max(0.1, (ward_info.get("bbox_north", 26.90) - ward_info.get("bbox_south", 26.80)) *
                    (ward_info.get("bbox_east", 81.00) - ward_info.get("bbox_west", 80.90)) * 111 * 111)

    # Drain density from ward
    drain_density = ward_info.get("drain_density", 3.0)

    # Spray gap (days since last spray event)
    spray_gap = 999  # Would come from spray_events table

    # Breeding score (composite)
    complaint_norm = 0.1  # Placeholder
    breeding_score = 0.4 * ndwi_stagnant_pct + 0.3 * water_persistence + 0.3 * complaint_norm

    return {
        "rain_7d_mm": round(rain_7d, 2),
        "rain_15d_mm": round(rain_15d, 2),
        "humidity_trend": round(humidity_trend, 4),
        "temp_anomaly": round(temp_anomaly, 2),
        "ndwi_change": round(ndwi_change, 4),
        "lst_diff": round(lst_diff, 2),
        "ndwi_stagnant_pct": round(ndwi_stagnant_pct, 4),
        "water_persistence_index": round(water_persistence, 4),
        "ndvi_mean": round(ndvi_mean, 4),
        "drain_density": round(drain_density, 2),
        "spray_gap_days": spray_gap,
        "breeding_score": round(breeding_score, 4),
        "rainfall_7d_mm": round(rain_7d, 2),
        "humidity_current": round(humidities[-1], 1) if humidities else 50.0,
        "temperature_current": round(temps[-1], 1) if temps else 28.0,
        "wind_speed": round(wind_speeds[-1], 1) if wind_speeds else 5.0,
    }
