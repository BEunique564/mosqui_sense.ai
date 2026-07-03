"""Ensemble risk fusion — CatBoost + TFT + NDWI (Module 7)."""

from dataclasses import dataclass

from app.core.config import settings


@dataclass
class EnsembleInput:
    catboost_probability: float
    tft_probability_15d: float
    ndwi_water_index: float  # 0-1 normalized


@dataclass
class EnsembleOutput:
    risk_score: float  # 0-100
    outbreak_probability: float  # 0-1


def fuse_risk_scores(inputs: EnsembleInput) -> EnsembleOutput:
    """
    Weighted ensemble calibrated for Lucknow pilot.
    Weights from SORA-style multi-source fusion + JAXA/Sophia RS lessons.
    """
    w_cb = settings.ensemble_weight_catboost
    w_tft = settings.ensemble_weight_tft
    w_ndwi = settings.ensemble_weight_ndwi

    outbreak_probability = (
        w_cb * inputs.catboost_probability
        + w_tft * inputs.tft_probability_15d
        + w_ndwi * inputs.ndwi_water_index
    )
    outbreak_probability = max(0.0, min(1.0, outbreak_probability))
    risk_score = outbreak_probability * 100.0

    return EnsembleOutput(
        risk_score=round(risk_score, 1),
        outbreak_probability=round(outbreak_probability, 4),
    )
