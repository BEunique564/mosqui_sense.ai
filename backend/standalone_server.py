"""
MosquiSense AI — Standalone FastAPI Server for Sadar Cantt, Lucknow.

Real-time mosquito outbreak prediction platform.
No Docker/PostgreSQL/Redis needed — uses SQLite + in-memory processing.

Run: python backend/standalone_server.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import Optional

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.database import (
    get_connection, init_db, seed_historical_weather, seed_historical_satellite
)
from backend.services.satellite_collector import get_live_satellite_status, download_mosdac_data
from backend.services.weather_service import get_current_weather, get_5day_forecast, get_weather_for_features
from backend.services.ndwi_processor import analyze_ward_ndwi
from backend.services.feature_engine import build_ward_features
from backend.services.prediction_engine import predict_outbreak
from backend.services.spray_optimizer import solve_spray_vrp, SADAR_CANTT_HOTSPOTS, DEPOT
from backend.services.citizen_service import submit_report, get_recent_reports, get_report_stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    conn = get_connection()
    ward = conn.execute("SELECT id FROM wards WHERE ward_code = 'SC-001'").fetchone()
    if ward:
        seed_historical_weather(ward["id"])
        seed_historical_satellite(ward["id"])
    conn.close()
    yield


app = FastAPI(
    title="MosquiSense AI — Sadar Cantt",
    description="Real-time mosquito outbreak prediction for Sadar Cantt, Lucknow using MOSDAC satellite data + AI ensemble",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    conn = get_connection()
    ward = conn.execute("SELECT id, name, center_lat, center_lon FROM wards WHERE ward_code = 'SC-001'").fetchone()
    pred_count = conn.execute("SELECT COUNT(*) as cnt FROM predictions").fetchone()["cnt"]
    weather_count = conn.execute("SELECT COUNT(*) as cnt FROM weather_history").fetchone()["cnt"]
    satellite_count = conn.execute("SELECT COUNT(*) as cnt FROM satellite_data").fetchone()["cnt"]
    report_count = conn.execute("SELECT COUNT(*) as cnt FROM citizen_reports").fetchone()["cnt"]
    conn.close()

    return {
        "status": "healthy",
        "service": "mosquisense-api",
        "version": "1.0.0",
        "location": "Sadar Cantt, Lucknow",
        "ward": dict(ward) if ward else None,
        "database": {
            "predictions": pred_count,
            "weather_records": weather_count,
            "satellite_records": satellite_count,
            "citizen_reports": report_count,
        },
    }


# ─── Ward Info ────────────────────────────────────────────────────────────────

@app.get("/v1/wards")
async def list_wards():
    conn = get_connection()
    wards = conn.execute("SELECT * FROM wards").fetchall()
    conn.close()
    return {"wards": [dict(w) for w in wards]}


@app.get("/v1/wards/sadar-cantt")
async def get_sadar_cantt_ward():
    conn = get_connection()
    ward = conn.execute("SELECT * FROM wards WHERE ward_code = 'SC-001'").fetchone()
    conn.close()
    if not ward:
        raise HTTPException(status_code=404, detail="Sadar Cantt ward not found")
    return dict(ward)


# ─── Weather ───────────────────────────────────────────────────────────────────

@app.get("/v1/weather/current")
async def weather_current():
    """Get real-time weather for Sadar Cantt from OpenWeatherMap."""
    result = get_current_weather()
    if result["status"] == "error":
        # Return stored weather if API not configured
        conn = get_connection()
        ward = conn.execute("SELECT id FROM wards WHERE ward_code = 'SC-001'").fetchone()
        if ward:
            latest = conn.execute(
                "SELECT * FROM weather_history WHERE ward_id = ? ORDER BY recorded_at DESC LIMIT 1",
                (ward["id"],)
            ).fetchone()
            conn.close()
            if latest:
                return {"status": "success", "source": "database_cache", **dict(latest)}
        conn.close()
    return result


@app.get("/v1/weather/forecast")
async def weather_forecast():
    """5-day weather forecast for Sadar Cantt."""
    return get_5day_forecast()


@app.get("/v1/weather/history")
async def weather_history(days: int = Query(default=30, ge=1, le=90)):
    """Historical weather data for Sadar Cantt."""
    conn = get_connection()
    ward = conn.execute("SELECT id FROM wards WHERE ward_code = 'SC-001'").fetchone()
    if not ward:
        conn.close()
        raise HTTPException(status_code=404, detail="Ward not found")

    rows = conn.execute(
        "SELECT * FROM weather_history WHERE ward_id = ? ORDER BY recorded_at DESC LIMIT ?",
        (ward["id"], days)
    ).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows], "count": len(rows)}


# ─── Satellite / NDWI ─────────────────────────────────────────────────────────

@app.get("/v1/satellite/status")
async def satellite_status():
    """MOSDAC satellite data availability and configuration status."""
    return get_live_satellite_status()


@app.get("/v1/satellite/ndwi")
async def satellite_ndwi():
    """Current NDWI water classification for Sadar Cantt."""
    conn = get_connection()
    ward = conn.execute("SELECT id FROM wards WHERE ward_code = 'SC-001'").fetchone()
    if not ward:
        conn.close()
        raise HTTPException(status_code=404, detail="Ward not found")

    rows = conn.execute(
        "SELECT * FROM satellite_data WHERE ward_id = ? ORDER BY recorded_at DESC LIMIT 30",
        (ward["id"],)
    ).fetchall()
    conn.close()

    ndwi_history = [dict(r) for r in rows]
    analysis = analyze_ward_ndwi(ndwi_history)

    return {
        "ward_code": "SC-001",
        "ward_name": "Sadar Cantt",
        "analysis": {
            "ndwi_mean": analysis.ndwi_mean,
            "water_class": analysis.water_class,
            "persistence_days": analysis.persistence_days,
            "stagnant_area_pct": analysis.stagnant_area_pct,
            "water_persistence_index": analysis.water_persistence_index,
            "breeding_risk": analysis.breeding_risk,
        },
        "history_count": len(ndwi_history),
        "latest_records": ndwi_history[:10],
    }


@app.get("/v1/satellite/history")
async def satellite_history(days: int = Query(default=30, ge=1, le=90)):
    """Historical satellite/NDWI data for Sadar Cantt."""
    conn = get_connection()
    ward = conn.execute("SELECT id FROM wards WHERE ward_code = 'SC-001'").fetchone()
    if not ward:
        conn.close()
        raise HTTPException(status_code=404, detail="Ward not found")

    rows = conn.execute(
        "SELECT * FROM satellite_data WHERE ward_id = ? ORDER BY recorded_at DESC LIMIT ?",
        (ward["id"], days)
    ).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows], "count": len(rows)}


@app.post("/v1/satellite/download")
async def trigger_satellite_download(dataset: str = "GSMaP_ISRO", days: int = 7):
    """Trigger MOSDAC satellite data download (requires credentials)."""
    return download_mosdac_data(dataset_id=dataset, days=days)


# ─── Predictions ───────────────────────────────────────────────────────────────

@app.get("/v1/predictions/wards/sadar-cantt")
async def get_sadar_cantt_prediction():
    """Get latest mosquito outbreak prediction for Sadar Cantt."""
    conn = get_connection()
    ward = conn.execute("SELECT * FROM wards WHERE ward_code = 'SC-001'").fetchone()
    if not ward:
        conn.close()
        raise HTTPException(status_code=404, detail="Ward not found")

    ward_id = ward["id"]

    # Get historical data for features
    weather_rows = conn.execute(
        "SELECT * FROM weather_history WHERE ward_id = ? ORDER BY recorded_at DESC LIMIT 30",
        (ward_id,)
    ).fetchall()
    sat_rows = conn.execute(
        "SELECT * FROM satellite_data WHERE ward_id = ? ORDER BY recorded_at DESC LIMIT 30",
        (ward_id,)
    ).fetchall()
    conn.close()

    features = build_ward_features(
        [dict(r) for r in weather_rows],
        [dict(r) for r in sat_rows],
        dict(ward),
    )

    prediction = predict_outbreak(ward_id, "SC-001", features)

    # Store prediction
    conn = get_connection()
    conn.execute("""
        INSERT INTO predictions (ward_id, risk_score, outbreak_probability, horizon_15d,
            model_version, top_drivers, predicted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        ward_id,
        prediction.risk_score,
        prediction.outbreak_probability,
        json.dumps(prediction.horizon_15d),
        prediction.model_version,
        json.dumps(prediction.top_drivers),
        prediction.timestamp,
    ))
    conn.commit()
    conn.close()

    return {
        "ward_code": prediction.ward_code,
        "ward_name": "Sadar Cantt",
        "risk_score": prediction.risk_score,
        "outbreak_probability": prediction.outbreak_probability,
        "breeding_risk": prediction.breeding_risk,
        "horizon_15d": prediction.horizon_15d,
        "model_version": prediction.model_version,
        "top_drivers": prediction.top_drivers,
        "model_breakdown": {
            "catboost_probability": prediction.catboost_prob,
            "tft_probability_15d": prediction.tft_prob,
            "ndwi_signal": prediction.ndwi_signal,
            "weights": {"catboost": 0.40, "tft": 0.35, "ndwi": 0.25},
        },
        "features_used": features,
        "timestamp": prediction.timestamp,
    }


@app.get("/v1/predictions/history")
async def prediction_history(limit: int = Query(default=30, ge=1, le=100)):
    """Prediction history for Sadar Cantt."""
    conn = get_connection()
    ward = conn.execute("SELECT id FROM wards WHERE ward_code = 'SC-001'").fetchone()
    if not ward:
        conn.close()
        raise HTTPException(status_code=404, detail="Ward not found")

    rows = conn.execute(
        "SELECT * FROM predictions WHERE ward_id = ? ORDER BY predicted_at DESC LIMIT ?",
        (ward["id"], limit)
    ).fetchall()
    conn.close()
    return {"data": [dict(r) for r in rows], "count": len(rows)}


@app.post("/v1/predictions/trigger")
async def trigger_prediction():
    """Manually trigger a new prediction run for Sadar Cantt."""
    return await get_sadar_cantt_prediction()


# ─── Spray Optimization ───────────────────────────────────────────────────────

@app.get("/v1/spray/hotspots")
async def get_hotspots():
    """Get Sadar Cantt spray hotspots with risk weights."""
    return {"hotspots": SADAR_CANTT_HOTSPOTS, "depot": DEPOT}


@app.post("/v1/spray/optimize")
async def optimize_spray(
    vehicle_count: int = Query(default=2, ge=1, le=5),
    hotspot_ids: Optional[list[str]] = Query(default=None),
):
    """Optimize fogging routes for Sadar Cantt using OR-Tools VRP."""
    from backend.services.spray_optimizer import VehicleSpec

    vehicles = [
        VehicleSpec(f"V{i+1}", 200.0, 40.0) for i in range(vehicle_count)
    ]

    result = solve_spray_vrp(
        hotspot_ids=hotspot_ids,
        vehicles=vehicles,
    )

    # Store route
    conn = get_connection()
    conn.execute("""
        INSERT INTO spray_routes (routes, total_fuel_liters, estimated_cost_inr, solver_status)
        VALUES (?, ?, ?, ?)
    """, (
        json.dumps([asdict(r) if hasattr(r, '__dataclass_fields__') else r for r in result.routes] if hasattr(result, 'routes') else result.routes),
        result.total_fuel_liters,
        result.estimated_cost_inr,
        result.solver_status,
    ))
    conn.commit()
    conn.close()

    return {
        "routes": [
            {
                "vehicle_id": r["vehicle_id"],
                "stops": r["stops"],
                "distance_km": r["distance_km"],
            } for r in result.routes
        ],
        "total_fuel_liters": result.total_fuel_liters,
        "estimated_cost_inr": result.estimated_cost_inr,
        "solver_status": result.solver_status,
        "total_distance_km": result.total_distance_km,
        "estimated_time_hours": result.estimated_time_hours,
        "vehicles_used": result.vehicles_used,
    }


# ─── Citizen Reports ──────────────────────────────────────────────────────────

@app.post("/v1/citizen/reports")
async def create_citizen_report(
    report_type: str = Query(..., pattern="^(mosquito|water_logging|drain|garbage)$"),
    latitude: float = Query(..., ge=26.0, le=28.0),
    longitude: float = Query(..., ge=80.0, le=82.0),
    severity: int = Query(..., ge=1, le=5),
    mosquito_density: int = Query(default=1, ge=1, le=5),
):
    """Submit a citizen report for Sadar Cantt area."""
    conn = get_connection()
    ward = conn.execute("SELECT id FROM wards WHERE ward_code = 'SC-001'").fetchone()
    if not ward:
        conn.close()
        raise HTTPException(status_code=404, detail="Ward not found")

    result = submit_report(
        conn=conn,
        ward_id=ward["id"],
        report_type=report_type,
        latitude=latitude,
        longitude=longitude,
        severity=severity,
        mosquito_density=mosquito_density,
    )
    conn.close()
    return result


@app.get("/v1/citizen/reports")
async def list_citizen_reports(limit: int = Query(default=20, ge=1, le=100)):
    """Get recent citizen reports for Sadar Cantt."""
    conn = get_connection()
    ward = conn.execute("SELECT id FROM wards WHERE ward_code = 'SC-001'").fetchone()
    if not ward:
        conn.close()
        raise HTTPException(status_code=404, detail="Ward not found")

    reports = get_recent_reports(conn, ward["id"], limit)
    stats = get_report_stats(conn, ward["id"])
    conn.close()
    return {"reports": reports, "stats": stats}


# ─── Dashboard Summary ────────────────────────────────────────────────────────

@app.get("/v1/dashboard/summary")
async def dashboard_summary():
    """Full dashboard summary for Sadar Cantt — all KPIs in one call."""
    conn = get_connection()
    ward = conn.execute("SELECT * FROM wards WHERE ward_code = 'SC-001'").fetchone()
    if not ward:
        conn.close()
        raise HTTPException(status_code=404, detail="Ward not found")

    ward_id = ward["id"]

    # Latest prediction
    pred = conn.execute(
        "SELECT * FROM predictions WHERE ward_id = ? ORDER BY predicted_at DESC LIMIT 1",
        (ward_id,)
    ).fetchone()

    # Report stats
    report_stats = get_report_stats(conn, ward_id)

    # Weather
    weather = conn.execute(
        "SELECT * FROM weather_history WHERE ward_id = ? ORDER BY recorded_at DESC LIMIT 1",
        (ward_id,)
    ).fetchone()

    # NDWI
    sat = conn.execute(
        "SELECT * FROM satellite_data WHERE ward_id = ? ORDER BY recorded_at DESC LIMIT 30",
        (ward_id,)
    ).fetchall()
    ndwi_analysis = analyze_ward_ndwi([dict(s) for s in sat])

    # Prediction count
    pred_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM predictions WHERE ward_id = ?", (ward_id,)
    ).fetchone()["cnt"]

    conn.close()

    return {
        "location": "Sadar Cantt, Lucknow",
        "ward": {
            "code": ward["ward_code"],
            "name": ward["name"],
            "population": ward["population"],
            "center": {"lat": ward["center_lat"], "lon": ward["center_lon"]},
        },
        "kpi": {
            "risk_score": pred["risk_score"] if pred else None,
            "outbreak_probability": pred["outbreak_probability"] if pred else None,
            "breeding_risk": "high" if pred and pred["risk_score"] > 50 else "moderate" if pred and pred["risk_score"] > 30 else "low",
            "active_hotspots": len(SADAR_CANTT_HOTSPOTS),
            "citizen_reports_total": report_stats.get("total_reports", 0),
            "mosquito_reports": report_stats.get("mosquito_reports", 0),
            "waterlogging_reports": report_stats.get("waterlogging_reports", 0),
            "model_version": pred["model_version"] if pred else "not_run",
            "predictions_run": pred_count,
        },
        "weather": dict(weather) if weather else None,
        "ndwi": {
            "water_class": ndwi_analysis.water_class,
            "stagnant_area_pct": ndwi_analysis.stagnant_area_pct,
            "breeding_risk": ndwi_analysis.breeding_risk,
            "persistence_days": ndwi_analysis.persistence_days,
        },
        "satellite_status": get_live_satellite_status(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─── Run Server ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    print(f"\n🦟 MosquiSense AI — Sadar Cantt, Lucknow")
    print(f"   API: http://{host}:{port}/docs")
    print(f"   Health: http://localhost:{port}/health")
    print(f"   Dashboard: http://localhost:{port}/v1/dashboard/summary\n")
    uvicorn.run(app, host=host, port=port, reload=True)
