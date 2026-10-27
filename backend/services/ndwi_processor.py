"""
NDWI Water Detection Processor — Real Sentinel-2 / MOSDAC integration.

NDWI = (Green - NIR) / (Green + NIR)

Water classification per Tiruchirappalli Sentinel-2 study:
    - No Water:      NDWI < 0
    - Moving Water:  NDWI >= 0, high temporal variance
    - Temporary:     NDWI >= 0.2, persistence < 7 days
    - Stagnant:      NDWI >= 0.2, persistence >= 7 days  (Aedes breeding risk!)
    - Flooded:       NDWI >= 0.5, ward-wide extent
"""

import numpy as np
from enum import Enum
from dataclasses import dataclass


class WaterClass(str, Enum):
    NO_WATER = "no_water"
    MOVING = "moving"
    TEMPORARY = "temporary"
    STAGNANT = "stagnant"
    FLOODED = "flooded"


STAGNATION_WEIGHTS = {
    WaterClass.NO_WATER: 0.0,
    WaterClass.MOVING: 0.2,
    WaterClass.TEMPORARY: 0.5,
    WaterClass.STAGNANT: 1.0,
    WaterClass.FLOODED: 0.8,
}


@dataclass
class NDWIResult:
    ndwi_mean: float
    water_class: str
    persistence_days: int
    stagnant_area_pct: float
    water_persistence_index: float
    breeding_risk: str


def compute_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Compute NDWI raster from Sentinel-2 B3 (green) and B8 (NIR)."""
    denominator = green.astype(float) + nir.astype(float)
    denominator = np.where(denominator == 0, np.nan, denominator)
    return (green.astype(float) - nir.astype(float)) / denominator


def classify_water_pixel(
    ndwi: float,
    persistence_days: int,
    temporal_variance: float,
) -> WaterClass:
    if np.isnan(ndwi) or ndwi < 0:
        return WaterClass.NO_WATER
    if temporal_variance > 0.05:
        return WaterClass.MOVING
    if ndwi >= 0.5 and persistence_days >= 3:
        return WaterClass.FLOODED
    if ndwi >= 0.2 and persistence_days >= 7:
        return WaterClass.STAGNANT
    if ndwi >= 0.2:
        return WaterClass.TEMPORARY
    return WaterClass.NO_WATER


def water_persistence_index(mean_ndwi: float, persistence_days: int, water_class: WaterClass) -> float:
    return mean_ndwi * persistence_days * STAGNATION_WEIGHTS[water_class] / 30.0


def analyze_ward_ndwi(ndwi_history: list[dict]) -> NDWIResult:
    """Analyze NDWI data for a ward over time and classify water bodies.

    Args:
        ndwi_history: List of dicts with keys: ndwi_mean, ndwi_stagnant_pct, recorded_at
    """
    if not ndwi_history:
        return NDWIResult(
            ndwi_mean=0.0,
            water_class=WaterClass.NO_WATER.value,
            persistence_days=0,
            stagnant_area_pct=0.0,
            water_persistence_index=0.0,
            breeding_risk="low",
        )

    ndwi_values = [d["ndwi_mean"] for d in ndwi_history]
    stagnant_pcts = [d.get("ndwi_stagnant_pct", 0) for d in ndwi_history]

    mean_ndwi = float(np.mean(ndwi_values))
    variance = float(np.var(ndwi_values))

    # Count consecutive days with NDWI >= 0.2 (stagnant threshold)
    persistence = 0
    for ndwi in reversed(ndwi_values):
        if ndwi >= 0.2:
            persistence += 1
        else:
            break

    avg_stagnant_pct = float(np.mean(stagnant_pcts))

    water_class = classify_water_pixel(mean_ndwi, persistence, variance)
    wpi = water_persistence_index(mean_ndwi, persistence, water_class)

    # Breeding risk assessment
    if water_class == WaterClass.STAGNANT and persistence >= 7 and avg_stagnant_pct > 0.15:
        breeding_risk = "critical"
    elif water_class in (WaterClass.STAGNANT, WaterClass.FLOODED) and persistence >= 3:
        breeding_risk = "high"
    elif water_class == WaterClass.TEMPORARY or mean_ndwi > 0:
        breeding_risk = "moderate"
    else:
        breeding_risk = "low"

    return NDWIResult(
        ndwi_mean=round(mean_ndwi, 4),
        water_class=water_class.value,
        persistence_days=persistence,
        stagnant_area_pct=round(avg_stagnant_pct, 4),
        water_persistence_index=round(wpi, 4),
        breeding_risk=breeding_risk,
    )
