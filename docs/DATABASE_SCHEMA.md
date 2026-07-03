# Database Schema — MosquiSense AI

PostgreSQL 16 + **PostGIS 3.4** + **TimescaleDB 2.x** + Redis 7.

---

## ER Diagram

```mermaid
erDiagram
    STATES ||--o{ DISTRICTS : contains
    DISTRICTS ||--o{ WARDS : contains
    WARDS ||--o{ WARD_BOUNDARIES : has
    WARDS ||--o{ PREDICTIONS : receives
    WARDS ||--o{ SPRAY_EVENTS : has
    WARDS ||--o{ COMPLAINTS : has
    WARDS ||--o{ WATER_POLYGONS : contains
    WARDS ||--o{ HOTSPOTS : identifies

    USERS ||--o{ SPRAY_EVENTS : operates
    USERS ||--o{ CITIZEN_REPORTS : submits
    USERS ||--o{ AUDIT_LOGS : generates

    SPRAY_EVENTS ||--o{ SPRAY_ROUTES : follows
    SPRAY_EVENTS }o--|| CHEMICALS : uses
    SPRAY_EVENTS }o--|| MACHINES : uses

    CITIZEN_REPORTS ||--o| CV_DETECTIONS : analyzed_by
    PREDICTIONS ||--o{ PREDICTION_EXPLANATIONS : explains

    SATELLITE_LAYERS ||--o{ WARD_SATELLITE_STATS : aggregates
    WEATHER_OBSERVATIONS ||--o{ WARD_WEATHER_STATS : aggregates

    STATES {
        uuid id PK
        string lgd_code UK
        string name
        geometry geom
    }

    DISTRICTS {
        uuid id PK
        uuid state_id FK
        string lgd_code UK
        string name
    }

    WARDS {
        uuid id PK
        uuid district_id FK
        string ward_code UK
        string name
        int population
        float drain_density
        geometry centroid
    }

    WARD_BOUNDARIES {
        uuid id PK
        uuid ward_id FK
        geometry geom
        date effective_from
    }

    USERS {
        uuid id PK
        string email UK
        string phone_hash
        enum role
        uuid ward_scope FK
        boolean mfa_enabled
    }

    PREDICTIONS {
        uuid id PK
        uuid ward_id FK
        timestamptz predicted_at
        float risk_score
        float outbreak_probability
        jsonb horizon_15d
        string model_version
    }

    SPRAY_EVENTS {
        uuid id PK
        uuid ward_id FK
        uuid operator_id FK
        date spray_date
        float fuel_liters
        float chemical_qty_kg
        uuid chemical_id FK
        uuid machine_id FK
        geometry route_geom
    }

    COMPLAINTS {
        uuid id PK
        uuid ward_id FK
        timestamptz reported_at
        enum severity
        geometry location
        string source
    }

    CITIZEN_REPORTS {
        uuid id PK
        uuid user_id FK
        uuid ward_id FK
        timestamptz reported_at
        enum report_type
        geometry location
        string photo_url
        int mosquito_density
        enum severity
    }

    CV_DETECTIONS {
        uuid id PK
        uuid report_id FK
        jsonb detections
        float confidence
        string model_version
    }

    WATER_POLYGONS {
        uuid id PK
        uuid ward_id FK
        enum water_class
        float ndwi_mean
        geometry geom
        date observed_date
    }

    HOTSPOTS {
        uuid id PK
        uuid ward_id FK
        timestamptz detected_at
        float cluster_score
        geometry geom
        date valid_until
    }

    SATELLITE_LAYERS {
        uuid id PK
        string dataset_id
        string product
        timestamptz acquired_at
        string storage_url
        geometry bbox
    }

    WEATHER_OBSERVATIONS {
        timestamptz time PK
        uuid ward_id FK
        float temperature
        float humidity
        float rainfall_mm
        float wind_speed
        float pressure
    }

    NOTIFICATIONS {
        uuid id PK
        uuid user_id FK
        enum channel
        enum alert_type
        timestamptz sent_at
        enum status
        jsonb payload
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        timestamptz action_at
        string action
        jsonb metadata
        inet ip_address
    }

    MODEL_REGISTRY {
        uuid id PK
        string model_name
        string version
        string mlflow_run_id
        timestamptz promoted_at
        enum stage
    }
```

---

## Core Tables (DDL Summary)

### Spatial Reference

All geometries stored as `GEOMETRY(MultiPolygon, 4326)` or `GEOMETRY(Point, 4326)`. Spatial index: `GIST (geom)`.

### `wards`

| Column | Type | Description |
|--------|------|-------------|
| ward_code | VARCHAR(20) | LMC ward identifier |
| population | INTEGER | Census 2011 + projected |
| drain_density | FLOAT | km drains / km² |
| centroid | POINT | Ward center for alerts |

### `predictions` (TimescaleDB hypertable on `predicted_at`)

| Column | Type | Description |
|--------|------|-------------|
| risk_score | FLOAT | 0-100 calibrated |
| outbreak_probability | FLOAT | 0-1 at day 15 |
| horizon_15d | JSONB | `[{day:1, prob:0.12}, ...]` |
| model_version | VARCHAR | MLflow version tag |

### `spray_events`

| Column | Type | Description |
|--------|------|-------------|
| fuel_liters | FLOAT | Diesel consumed |
| chemical_qty_kg | FLOAT | Larvicide/fogging chemical |
| route_geom | LINESTRING | GPS-tracked fogging route |

### `water_polygons`

| Column | Type | Description |
|--------|------|-------------|
| water_class | ENUM | no_water, moving, temporary, stagnant, flooded |
| ndwi_mean | FLOAT | Mean NDWI within polygon |

### `citizen_reports`

| Column | Type | Description |
|--------|------|-------------|
| report_type | ENUM | mosquito, water_logging, drain, garbage |
| mosquito_density | INT | 1-5 citizen scale |
| photo_url | TEXT | S3/Blob path (EXIF stripped) |

---

## Redis Key Schema

| Key Pattern | TTL | Purpose |
|-------------|-----|---------|
| `risk:ward:{id}` | 1h | Latest risk score cache |
| `forecast:ward:{id}` | 6h | 15-day TFT output |
| `heatmap:tiles:{z}:{x}:{y}` | 24h | Map tile cache |
| `celery-task:{id}` | — | Task status |
| `alert:sent:{user}:{date}` | 24h | Dedup citizen alerts |

---

## Feature Store (Feast)

**Entity:** `ward_id`  
**Feature views:**

| View | Features | TTL |
|------|----------|-----|
| `weather_features` | temp, humidity, rain_7d, rain_15d, humidity_trend | 1 day |
| `satellite_features` | lst, ndwi, ndwi_change, vegetation | 3 days |
| `municipal_features` | spray_gap, complaint_density, last_chemical | 1 day |
| `engineered_features` | breeding_score, drain_score, water_persistence | 1 day |

---

## Indexing Strategy

```sql
CREATE INDEX idx_predictions_ward_time ON predictions (ward_id, predicted_at DESC);
CREATE INDEX idx_spray_ward_date ON spray_events (ward_id, spray_date DESC);
CREATE INDEX idx_complaints_ward_time ON complaints (ward_id, reported_at DESC);
CREATE INDEX idx_water_polygons_geom ON water_polygons USING GIST (geom);
CREATE INDEX idx_hotspots_active ON hotspots (ward_id, valid_until) WHERE valid_until >= CURRENT_DATE;
```

---

## Partitioning (State/National Scale)

- `predictions` — partition by `district_id` (Postgres declarative partitioning)
- `weather_observations` — TimescaleDB chunk interval 7 days
- `audit_logs` — monthly partitions, 7-year retention (government compliance)

---

## Migration Path

Migrations managed by **Alembic** in `database/migrations/`. Initial seed: Lucknow ward shapefiles from LMC Open Data + LGD codes.
