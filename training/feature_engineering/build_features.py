"""Advanced feature engineering for MosquiSense AI."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class FeatureConfig:
    ward_id: str
    reference_date: pd.Timestamp


def rolling_rainfall(df: pd.DataFrame, window: int) -> pd.Series:
    return df["rainfall_mm"].rolling(window=window, min_periods=1).sum()


def humidity_trend(df: pd.DataFrame, window: int = 7) -> float:
    if len(df) < 2:
        return 0.0
    recent = df["humidity"].tail(window).values
    x = np.arange(len(recent))
    slope, _ = np.polyfit(x, recent, 1)
    return float(slope)


def temperature_anomaly(df: pd.DataFrame, climatology: dict[int, float]) -> float:
    month = df["date"].iloc[-1].month
    baseline = climatology.get(month, df["temperature"].mean())
    return float(df["temperature"].iloc[-1] - baseline)


def spray_gap_days(last_spray_date: pd.Timestamp | None, reference: pd.Timestamp) -> int:
    if last_spray_date is None:
        return 999
    return (reference - last_spray_date).days


def complaint_density(count: int, ward_area_km2: float, window_days: int = 7) -> float:
    if ward_area_km2 <= 0:
        return 0.0
    return count / ward_area_km2 / window_days


def breeding_score(ndwi_stagnant_pct: float, water_persistence: float, complaint_norm: float) -> float:
    return 0.4 * ndwi_stagnant_pct + 0.3 * water_persistence + 0.3 * complaint_norm


def build_ward_features(
    weather_df: pd.DataFrame,
    satellite_stats: dict,
    municipal_stats: dict,
    config: FeatureConfig,
) -> dict:
    """Build single-row feature dict for CatBoost / TFT."""
    climatology = municipal_stats.get("temp_climatology", {})
    return {
        "ward_id": config.ward_id,
        "date": config.reference_date.isoformat(),
        "rain_7d_mm": float(rolling_rainfall(weather_df, 7).iloc[-1]),
        "rain_15d_mm": float(rolling_rainfall(weather_df, 15).iloc[-1]),
        "humidity_trend": humidity_trend(weather_df),
        "temp_anomaly": temperature_anomaly(weather_df, climatology),
        "ndwi_change": satellite_stats.get("ndwi_change", 0.0),
        "lst_diff": satellite_stats.get("lst_diff", 0.0),
        "complaint_density": complaint_density(
            municipal_stats.get("complaint_count_7d", 0),
            municipal_stats.get("ward_area_km2", 1.0),
        ),
        "spray_gap_days": spray_gap_days(
            municipal_stats.get("last_spray_date"),
            config.reference_date,
        ),
        "breeding_score": breeding_score(
            satellite_stats.get("ndwi_stagnant_pct", 0.0),
            satellite_stats.get("water_persistence_index", 0.0),
            municipal_stats.get("complaint_norm", 0.0),
        ),
        "drain_score": municipal_stats.get("drain_density", 0.0)
        * municipal_stats.get("open_drain_cv_pct", 0.0),
        "vegetation_score": satellite_stats.get("ndvi_mean", 0.0),
        "water_persistence_index": satellite_stats.get("water_persistence_index", 0.0),
    }
