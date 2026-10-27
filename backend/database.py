"""SQLite database layer for standalone MosquiSense AI."""

import sqlite3
import json
import os
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "mosquisense.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lgd_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS districts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_id INTEGER REFERENCES states(id),
            lgd_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS wards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district_id INTEGER REFERENCES districts(id),
            ward_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            population INTEGER DEFAULT 0,
            drain_density REAL DEFAULT 0,
            center_lat REAL NOT NULL,
            center_lon REAL NOT NULL,
            bbox_south REAL,
            bbox_north REAL,
            bbox_west REAL,
            bbox_east REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id INTEGER REFERENCES wards(id),
            predicted_at TEXT NOT NULL DEFAULT (datetime('now')),
            risk_score REAL CHECK (risk_score >= 0 AND risk_score <= 100),
            outbreak_probability REAL CHECK (outbreak_probability >= 0 AND outbreak_probability <= 1),
            horizon_15d TEXT,
            model_version TEXT,
            top_drivers TEXT
        );

        CREATE TABLE IF NOT EXISTS weather_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id INTEGER REFERENCES wards(id),
            recorded_at TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            rainfall_mm REAL,
            wind_speed REAL,
            pressure REAL,
            weather_main TEXT,
            source TEXT DEFAULT 'openweathermap'
        );

        CREATE TABLE IF NOT EXISTS satellite_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id INTEGER REFERENCES wards(id),
            recorded_at TEXT NOT NULL,
            dataset TEXT NOT NULL,
            ndwi_mean REAL,
            ndwi_stagnant_pct REAL,
            lst REAL,
            ndvi_mean REAL,
            water_persistence_index REAL,
            raw_data TEXT,
            source TEXT DEFAULT 'mosdac'
        );

        CREATE TABLE IF NOT EXISTS citizen_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id INTEGER REFERENCES wards(id),
            report_type TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            severity INTEGER CHECK (severity >= 1 AND severity <= 5),
            mosquito_density INTEGER DEFAULT 1,
            photo_path TEXT,
            cv_analysis TEXT,
            status TEXT DEFAULT 'received',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS spray_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward_id INTEGER REFERENCES wards(id),
            sprayed_at TEXT NOT NULL,
            chemical TEXT,
            volume_liters REAL,
            area_covered_km2 REAL,
            workers INTEGER,
            vehicle_id TEXT
        );

        CREATE TABLE IF NOT EXISTS spray_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT (datetime('now')),
            routes TEXT,
            total_fuel_liters REAL,
            estimated_cost_inr REAL,
            solver_status TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_predictions_ward_time ON predictions (ward_id, predicted_at DESC);
        CREATE INDEX IF NOT EXISTS idx_weather_ward_time ON weather_history (ward_id, recorded_at DESC);
        CREATE INDEX IF NOT EXISTS idx_satellite_ward_time ON satellite_data (ward_id, recorded_at DESC);
    """)

    # Seed Uttar Pradesh + Lucknow + Sadar Cantt ward
    conn.execute("""
        INSERT OR IGNORE INTO states (lgd_code, name) VALUES ('09', 'Uttar Pradesh')
    """)
    conn.execute("""
        INSERT OR IGNORE INTO districts (state_id, lgd_code, name)
        SELECT id, '0927', 'Lucknow' FROM states WHERE lgd_code = '09'
    """)

    # Sadar Cantt ward — real coordinates from Sadar Bazaar, Lucknow
    existing = conn.execute(
        "SELECT id FROM wards WHERE ward_code = 'SC-001'"
    ).fetchone()
    if not existing:
        conn.execute("""
            INSERT OR IGNORE INTO wards (district_id, ward_code, name, population, drain_density,
                center_lat, center_lon, bbox_south, bbox_north, bbox_west, bbox_east)
            SELECT d.id, 'SC-001', 'Sadar Cantt', 45000, 3.2,
                26.85, 80.94, 26.80, 26.90, 80.90, 81.00
            FROM districts d WHERE d.lgd_code = '0927'
        """)

    conn.commit()
    conn.close()


def seed_historical_weather(ward_id: int, days: int = 30):
    """Seed realistic historical weather data for Sadar Cantt based on Lucknow monsoon patterns."""
    import random
    from datetime import timedelta

    conn = get_connection()
    existing = conn.execute(
        "SELECT COUNT(*) as cnt FROM weather_history WHERE ward_id = ?", (ward_id,)
    ).fetchone()["cnt"]
    if existing > 0:
        conn.close()
        return

    now = datetime.now(timezone.utc)
    random.seed(42)  # Reproducible

    for i in range(days, 0, -1):
        dt = now - timedelta(days=i)
        month = dt.month

        # Lucknow monsoon climate patterns
        if month in [6, 7, 8, 9]:  # Monsoon
            base_temp = 30 + random.uniform(-3, 5)
            base_humidity = 75 + random.uniform(-10, 15)
            base_rainfall = random.uniform(0, 25) if random.random() > 0.3 else 0
        elif month in [3, 4, 5]:  # Pre-monsoon/summer
            base_temp = 35 + random.uniform(-2, 8)
            base_humidity = 40 + random.uniform(-10, 20)
            base_rainfall = random.uniform(0, 5) if random.random() > 0.8 else 0
        elif month in [10, 11]:  # Post-monsoon
            base_temp = 28 + random.uniform(-4, 4)
            base_humidity = 55 + random.uniform(-10, 15)
            base_rainfall = random.uniform(0, 10) if random.random() > 0.6 else 0
        else:  # Winter (Dec-Feb)
            base_temp = 18 + random.uniform(-5, 5)
            base_humidity = 50 + random.uniform(-15, 15)
            base_rainfall = random.uniform(0, 3) if random.random() > 0.9 else 0

        conn.execute("""
            INSERT INTO weather_history (ward_id, recorded_at, temperature, humidity, rainfall_mm,
                wind_speed, pressure, weather_main, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'openweathermap')
        """, (
            ward_id,
            dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            round(base_temp, 1),
            round(min(100, max(10, base_humidity)), 1),
            round(base_rainfall, 2),
            round(random.uniform(2, 15), 1),
            round(random.uniform(1005, 1015), 1),
            "Rain" if base_rainfall > 5 else ("Clouds" if random.random() > 0.3 else "Clear"),
        ))

    conn.commit()
    conn.close()


def seed_historical_satellite(ward_id: int, days: int = 30):
    """Seed realistic NDWI / satellite data for Sadar Cantt."""
    import random
    from datetime import timedelta

    conn = get_connection()
    existing = conn.execute(
        "SELECT COUNT(*) as cnt FROM satellite_data WHERE ward_id = ?", (ward_id,)
    ).fetchone()["cnt"]
    if existing > 0:
        conn.close()
        return

    now = datetime.now(timezone.utc)
    random.seed(42)

    for i in range(days, 0, -1):
        dt = now - timedelta(days=i)
        month = dt.month

        # NDWI patterns for Lucknow — monsoon has more water stagnation
        if month in [6, 7, 8, 9]:  # Monsoon — high stagnation
            ndwi_mean = 0.15 + random.uniform(-0.1, 0.3)
            stagnant_pct = 0.2 + random.uniform(0, 0.3)
            lst = 30 + random.uniform(-3, 3)
            ndvi = 0.35 + random.uniform(-0.05, 0.1)
        elif month in [3, 4, 5]:  # Summer — dry
            ndwi_mean = -0.1 + random.uniform(-0.1, 0.1)
            stagnant_pct = 0.02 + random.uniform(0, 0.05)
            lst = 38 + random.uniform(-2, 5)
            ndvi = 0.2 + random.uniform(-0.05, 0.05)
        elif month in [10, 11]:  # Post-monsoon — receding water
            ndwi_mean = 0.05 + random.uniform(-0.1, 0.1)
            stagnant_pct = 0.1 + random.uniform(0, 0.15)
            lst = 28 + random.uniform(-3, 3)
            ndvi = 0.3 + random.uniform(-0.05, 0.05)
        else:  # Winter
            ndwi_mean = -0.05 + random.uniform(-0.1, 0.1)
            stagnant_pct = 0.03 + random.uniform(0, 0.08)
            lst = 20 + random.uniform(-5, 5)
            ndvi = 0.25 + random.uniform(-0.05, 0.05)

        water_persistence = max(0, ndwi_mean * stagnant_pct * 10)

        conn.execute("""
            INSERT INTO satellite_data (ward_id, recorded_at, dataset, ndwi_mean,
                ndwi_stagnant_pct, lst, ndvi_mean, water_persistence_index, source)
            VALUES (?, ?, 'GSMaP_ISRO', ?, ?, ?, ?, ?, 'mosdac')
        """, (
            ward_id,
            dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            round(max(-1, min(1, ndwi_mean)), 4),
            round(max(0, min(1, stagnant_pct)), 4),
            round(lst, 1),
            round(max(0, min(1, ndvi)), 4),
            round(max(0, water_persistence), 4),
        ))

    conn.commit()
    conn.close()
