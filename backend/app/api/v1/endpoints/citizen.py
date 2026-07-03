"""Citizen reporting endpoints — Module 4."""

from enum import Enum

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field

router = APIRouter()


class ReportType(str, Enum):
    mosquito = "mosquito"
    water_logging = "water_logging"
    drain = "drain"
    garbage = "garbage"


class CitizenReportResponse(BaseModel):
    report_id: str
    status: str
    cv_analysis_queued: bool


@router.post("/reports", response_model=CitizenReportResponse)
async def submit_report(
    report_type: ReportType = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    severity: int = Form(..., ge=1, le=5),
    mosquito_density: int = Form(default=1, ge=1, le=5),
    photo: UploadFile | None = File(default=None),
):
    """Submit citizen report with optional photo for YOLOv11 analysis."""
    return CitizenReportResponse(
        report_id="pending",
        status="received",
        cv_analysis_queued=photo is not None,
    )
