"""Ensemble fusion unit tests."""

from app.services.prediction.ensemble import EnsembleInput, fuse_risk_scores


def test_fuse_risk_scores_weighted():
    result = fuse_risk_scores(
        EnsembleInput(
            catboost_probability=0.8,
            tft_probability_15d=0.7,
            ndwi_water_index=0.6,
        )
    )
    expected = 0.4 * 0.8 + 0.35 * 0.7 + 0.25 * 0.6
    assert abs(result.outbreak_probability - expected) < 0.001
    assert abs(result.risk_score - expected * 100) < 0.1


def test_fuse_risk_scores_clamped():
    result = fuse_risk_scores(
        EnsembleInput(catboost_probability=1.5, tft_probability_15d=0.5, ndwi_water_index=0.5)
    )
    assert result.outbreak_probability <= 1.0
    assert result.risk_score <= 100.0
