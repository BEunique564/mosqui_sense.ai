"""
Citizen Report Service — Handles citizen mosquito/waterlogging reports.

Includes mock YOLOv11 CV analysis for photo submissions.
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"


@dataclass
class CitizenReport:
    id: int
    ward_id: int
    report_type: str
    latitude: float
    longitude: float
    severity: int
    mosquito_density: int
    photo_path: Optional[str]
    cv_analysis: Optional[dict]
    status: str
    created_at: str


def analyze_photo(photo_path: str) -> dict:
    """
    Mock YOLOv11 analysis for citizen-submitted photos.

    In production, this runs ultralytics YOLO on the image.
    For standalone demo, returns realistic analysis based on report type.
    """
    # In production: from ultralytics import YOLO; model = YOLO('yolo11n.pt')
    return {
        "model": "YOLOv11n-mosquitov2",
        "detections": [
            {"class": "standing_water", "confidence": 0.87, "bbox": [120, 200, 350, 400]},
            {"class": "mosquito_larvae", "confidence": 0.72, "bbox": [180, 250, 220, 280]},
        ],
        "risk_level": "high",
        "recommendation": "Immediate fogging recommended — standing water with larval activity detected",
        "exif_stripped": True,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def submit_report(
    conn,
    ward_id: int,
    report_type: str,
    latitude: float,
    longitude: float,
    severity: int,
    mosquito_density: int = 1,
    photo_path: Optional[str] = None,
) -> dict:
    """Submit a citizen report with optional photo analysis."""
    cv_analysis = None
    if photo_path and os.path.exists(photo_path):
        cv_analysis = analyze_photo(photo_path)

    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute("""
        INSERT INTO citizen_reports (ward_id, report_type, latitude, longitude,
            severity, mosquito_density, photo_path, cv_analysis, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'received', ?)
    """, (ward_id, report_type, latitude, longitude, severity, mosquito_density,
          photo_path, str(cv_analysis) if cv_analysis else None, now))

    conn.commit()
    report_id = cursor.lastrowid

    return {
        "report_id": report_id,
        "status": "received",
        "cv_analysis_queued": photo_path is not None,
        "cv_result": cv_analysis,
        "created_at": now,
    }


def get_recent_reports(conn, ward_id: int, limit: int = 20) -> list[dict]:
    """Get recent citizen reports for a ward."""
    rows = conn.execute("""
        SELECT * FROM citizen_reports WHERE ward_id = ?
        ORDER BY created_at DESC LIMIT ?
    """, (ward_id, limit)).fetchall()

    return [dict(r) for r in rows]


def get_report_stats(conn, ward_id: int) -> dict:
    """Get aggregated report statistics."""
    stats = conn.execute("""
        SELECT
            COUNT(*) as total_reports,
            SUM(CASE WHEN report_type = 'mosquito' THEN 1 ELSE 0 END) as mosquito_reports,
            SUM(CASE WHEN report_type = 'water_logging' THEN 1 ELSE 0 END) as waterlogging_reports,
            SUM(CASE WHEN report_type = 'drain' THEN 1 ELSE 0 END) as drain_reports,
            SUM(CASE WHEN report_type = 'garbage' THEN 1 ELSE 0 END) as garbage_reports,
            AVG(severity) as avg_severity,
            MAX(created_at) as latest_report
        FROM citizen_reports WHERE ward_id = ?
    """, (ward_id,)).fetchone()

    return dict(stats) if stats else {}
