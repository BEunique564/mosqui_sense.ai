"""
NDWI Water Detection — Module 5.

NDWI = (Green - NIR) / (Green + NIR)

Water classification:
    - No Water:      NDWI < 0
    - Moving Water:  NDWI >= 0, high temporal variance
    - Temporary:     NDWI >= 0.2, persistence < 7 days
    - Stagnant:      NDWI >= 0.2, persistence >= 7 days  (Aedes breeding risk)
    - Flooded:       NDWI >= 0.5, ward-wide extent

Reference: Tiruchirappalli Sentinel-2 study (InfoNTD).
"""

from enum import Enum

import numpy as np


class WaterClass(str, Enum):
    NO_WATER = "no_water"
    MOVING = "moving"
    TEMPORARY = "temporary"
    STAGNANT = "stagnant"
    FLOODED = "flooded"


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


STAGNATION_WEIGHTS = {
    WaterClass.NO_WATER: 0.0,
    WaterClass.MOVING: 0.2,
    WaterClass.TEMPORARY: 0.5,
    WaterClass.STAGNANT: 1.0,
    WaterClass.FLOODED: 0.8,
}


def water_persistence_index(mean_ndwi: float, persistence_days: int, water_class: WaterClass) -> float:
    """Composite index for Module 7 feature store."""
    return mean_ndwi * persistence_days * STAGNATION_WEIGHTS[water_class] / 30.0
