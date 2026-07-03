"""Prediction endpoints — Module 7 output."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class HorizonDay(BaseModel):
    day: int
    probability: float = Field(ge=0, le=1)


class FeatureDriver(BaseModel):
    feature: str
    impact: float


class WardPrediction(BaseModel):
    ward_id: UUID
    ward_code: str
    risk_score: float = Field(ge=0, le=100)
    outbreak_probability_15d: float = Field(ge=0, le=1)
    horizon: list[HorizonDay]
    model_version: str
    top_drivers: list[FeatureDriver]


@router.get("/wards/{ward_id}", response_model=WardPrediction)
async def get_ward_prediction(ward_id: UUID):
    """Return latest risk score and 15-day forecast for a ward."""
    raise HTTPException(
        status_code=501,
        detail="Connect feature store and ML inference service (Phase 1 MVP)",
    )


@router.post("/trigger")
async def trigger_prediction_run():
    """Manual async inference — enqueues Celery task."""
    return {"status": "queued", "task": "prediction.run_daily"}
