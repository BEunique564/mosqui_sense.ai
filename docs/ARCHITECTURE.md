# MosquiSense AI — System Architecture

Government-grade smart city platform for predictive mosquito vector control. Initial deployment: **Lucknow, Uttar Pradesh**. Architecture supports horizontal scaling to **UP** and **India** without redesign.

---

## 1. High-Level Architecture

```mermaid
flowchart TB
    subgraph DataSources["Data Sources"]
        MOSDAC[MOSDAC Satellite Collector]
        Weather[IMD / OpenWeather API]
        MunDB[Municipality Records]
        Citizen[Citizen Reporting App]
        Sentinel[Sentinel-2 NDWI Pipeline]
    end

    subgraph Ingestion["Ingestion Layer — Kafka"]
        K1[satellite.raw]
        K2[weather.raw]
        K3[municipality.events]
        K4[citizen.reports]
    end

    subgraph Processing["Processing — Celery Workers"]
        Clean[Data Cleaning]
        FE[Feature Engineering]
        NDWI[NDWI Water Classifier]
        CV[YOLOv11 CV Pipeline]
    end

    subgraph Storage["Storage"]
        PG[(PostgreSQL + PostGIS)]
        TS[(TimescaleDB — time series)]
        Redis[(Redis — cache + Celery)]
        FS[(Feature Store — Feast)]
        MLflow[(MLflow — model registry)]
        S3[(Object Storage — rasters/images)]
    end

    subgraph AI["AI Layer"]
        TFT[TFT — 15-day forecast]
        CB[CatBoost — ward risk]
        UNET[U-Net + NDWI]
        ENS[Ensemble Fusion]
        OR[OR-Tools VRP]
    end

    subgraph Apps["Application Layer"]
        API[FastAPI Gateway]
        Dash[Next.js Dashboard]
        Notify[Notification Service]
    end

    subgraph GIS["GIS Layer"]
        GeoServer[GeoServer WMS/WFS]
        PostGIS[PostGIS Spatial Queries]
    end

    MOSDAC --> K1
    Weather --> K2
    MunDB --> K3
    Citizen --> K4
    Sentinel --> K1

    K1 & K2 & K3 & K4 --> Clean --> FE --> FS
    FE --> NDWI & CV

    FS --> TFT & CB
    NDWI --> UNET --> FS
    CV --> FS
    TFT & CB & UNET --> ENS
    ENS --> PG & TS
    ENS --> OR

    PG --> PostGIS --> GeoServer
    API --> PG & Redis & FS & MLflow
    API --> ENS & OR
    Dash --> API & GeoServer
    Notify --> API
```

---

## 2. Data Flow Diagram

```mermaid
flowchart LR
    A[Satellite Download] --> B[Normalize to Ward Grid]
    C[Weather 15-day Forecast] --> B
    D[Spray / Complaint Records] --> B
    E[Citizen GPS + Photos] --> F[CV + Geo Validation]
    F --> B
    G[Sentinel NDWI] --> H[Water Polygons]
    H --> B

    B --> I[Feature Store]
    I --> J[Batch Inference Daily]
    J --> K[Risk Score 0-100]
    J --> L[Outbreak Probability]
    K --> M[Heatmap Tiles]
    L --> N[Hotspot ST-DBSCAN]
    K --> O[OR-Tools Spray Plan]
    M & N & O --> P[Municipality Dashboard]
    K --> Q[Citizen Alerts]
    Q --> R[Feedback Loop]
    R --> I
```

---

## 3. Microservices Architecture

| Service | Responsibility | Tech |
|---------|----------------|------|
| `api-gateway` | Auth, routing, rate limit | FastAPI + JWT |
| `satellite-collector` | MOSDAC auto-download | Python + mdapi |
| `weather-collector` | IMD + forecast ingest | Celery beat |
| `ndwi-processor` | Sentinel NDWI polygons | GDAL + U-Net |
| `cv-processor` | Citizen image analysis | YOLOv11 |
| `feature-engine` | Rolling features, anomalies | Pandas + Feast |
| `prediction-service` | TFT + CatBoost + ensemble | PyTorch + CatBoost |
| `optimization-service` | VRP, resource allocation | OR-Tools |
| `notification-service` | SMS, WhatsApp, push, IVR | Twilio, FCM, NIC gateway |
| `gis-service` | GeoServer proxy, tile cache | GeoServer + Redis |
| `analytics-service` | KPIs, cost savings | TimescaleDB queries |
| `retraining-worker` | Weekly/monthly MLflow runs | Celery + DVC |

All services share:
- **PostgreSQL/PostGIS** for transactional + spatial data
- **TimescaleDB** extension for sensor/time-series hypertables
- **Redis** for cache, Celery broker, pub/sub alerts
- **Kafka** for event streaming at state/national scale

---

## 4. Sequence Diagram — Daily Prediction Cycle

```mermaid
sequenceDiagram
    participant Cron as Celery Beat
    participant Sat as Satellite Collector
    participant W as Weather API
    participant FE as Feature Engine
    participant FS as Feature Store
    participant ML as Prediction Service
    participant OR as OR-Tools
    participant DB as PostgreSQL
    participant N as Notification Service
    participant D as Dashboard

    Cron->>Sat: Trigger MOSDAC download (06:00 IST)
    Cron->>W: Fetch 15-day forecast
    Sat->>FE: LST, rainfall, vegetation rasters
    W->>FE: Hourly + daily forecast
    FE->>FS: Write ward-level features
    FS->>ML: Load feature vector per ward
    ML->>ML: TFT horizon + CatBoost tabular
    ML->>ML: Ensemble fusion → risk 0-100
    ML->>DB: Persist predictions + explainability
    ML->>OR: Top-N high-risk wards
    OR->>DB: Spray routes, fuel estimate
    DB->>D: Push WebSocket update
    ML->>N: Risk threshold exceeded?
    N->>N: SMS / WhatsApp / Push to citizens
```

---

## 5. Deployment Diagram

```mermaid
flowchart TB
    subgraph Dev["Development — RTX 3050"]
        GPU[Local GPU Training]
        Docker[Docker Compose]
    end

    subgraph Cloud["Production — Azure / NIC Cloud"]
        LB[Load Balancer]
        K8s[Kubernetes Cluster]
        subgraph Pods
            APIp[API Pods x3]
            MLp[ML Inference x2]
            Cel[Celery Workers x5]
        end
        RDS[(PostgreSQL HA)]
        RedisC[(Redis Cluster)]
        KafkaC[(Kafka Cluster)]
        Blob[Blob Storage]
        MLflowS[MLflow Server]
    end

    subgraph Edge["Municipal Edge — Lucknow"]
        Field[Field Tablets — GPS routes]
        IVR[IVR Gateway]
    end

    Dev -->|CI/CD GitHub Actions| Cloud
    LB --> APIp
    APIp --> RDS & RedisC
    MLp --> MLflowS & Blob
    Cel --> KafkaC
    Field --> LB
    IVR --> LB
```

---

## 6. Scalability Path (No Architecture Change)

| Stage | Wards | Strategy |
|-------|-------|----------|
| MVP | 1 | Single Celery worker, local Feast |
| Pilot | 10 | Partition Kafka by ward_id |
| Lucknow | ~110 | HPA on inference pods, read replicas |
| UP | ~4,000 | Multi-region K8s, ward sharding in PostGIS |
| India | ~50,000+ | State-level Kafka topics, federated feature store |

**Sharding key:** `state_code + district_code + ward_id` (Bharat geo codes aligned with LGD).

---

## 7. Security Architecture

| Layer | Control |
|-------|---------|
| Authentication | JWT (RS256), refresh tokens, MFA for admins |
| Authorization | RBAC: `super_admin`, `state_admin`, `municipal_officer`, `field_operator`, `citizen`, `analyst` |
| Data at rest | AES-256 (PostgreSQL TDE, blob encryption) |
| Data in transit | TLS 1.3, mTLS between services |
| Audit | Immutable audit log table + SIEM export |
| PII | Citizen phone hashed, photos EXIF-stripped, DPDP Act 2023 compliance |
| Government | STQC-ready logging, air-gapped deployment option |

---

## 8. Backend Stack Detail

```
FastAPI (async) ──► Pydantic v2 schemas
       │
       ├── SQLAlchemy 2.0 + GeoAlchemy2 (PostGIS)
       ├── Celery 5.x + Redis broker
       ├── Kafka (confluent-kafka) — scale path
       └── Prometheus metrics → Grafana dashboards
```

**Clean Architecture layers:**
- `domain/` — entities, value objects (Ward, RiskScore, SprayEvent)
- `application/` — use cases (PredictOutbreak, OptimizeRoute)
- `infrastructure/` — DB repos, MOSDAC client, ML adapters
- `presentation/` — FastAPI routers, WebSocket handlers

---

## 9. Frontend Stack Detail

```
Next.js 14 (App Router)
  ├── React 18 + TypeScript
  ├── Tailwind CSS + shadcn/ui (government accessibility)
  ├── Leaflet + Mapbox GL (ward heatmaps)
  ├── Chart.js (analytics)
  └── React Query (server state)
```

**Dashboard modules:** Risk overview, 15-day forecast, heatmap, spray analytics, fuel/cost savings, complaint trends, satellite layers, weather overlay.

---

## 10. MLOps Pipeline

```mermaid
flowchart LR
    DVC[DVC Data Versioning] --> Train[Training Job]
    Train --> MLflow[MLflow Tracking]
    MLflow --> Reg[Model Registry]
    Reg --> Staging[Staging Deploy]
    Staging --> Val[Backtest + A/B]
    Val --> Prod[Production Promote]
    Prod --> Prom[Prometheus Drift Monitor]
    Prom -->|Drift detected| Retrain[Auto Retrain Trigger]
```

**Retraining schedule:**
- Weekly: CatBoost incremental (new complaints + spray data)
- Monthly: Full TFT retrain with expanded window
- Manual: MLflow run from dashboard (monsoon onset)

---

## 11. GIS Engine

| Component | Role |
|-----------|------|
| PostGIS | Ward boundaries, hotspots, water polygons, routes |
| QGIS | Offline municipal cartography, shapefile import |
| GeoServer | WMS/WFS layers for dashboard |
| Leaflet/Mapbox | Interactive citizen + officer maps |

**Coordinate system:** EPSG:4326 (WGS84) storage, EPSG:7755 (India NSIG) for distance calculations in UP.

---

## 12. Hardware — RTX 3050 Development Profile

| Parameter | Recommendation |
|-----------|----------------|
| GPU VRAM | 4 GB — limits batch sizes |
| Mixed precision | `torch.cuda.amp` autocast FP16 for TFT/U-Net |
| TFT batch size | 32 (hidden_size=64, num_heads=4) |
| U-Net | ResNet34 encoder, batch 8, 512×512 patches |
| YOLOv11 | `yolo11n.pt` — train batch 16, imgsz 640 |
| CatBoost | CPU training — no GPU needed, `iterations=2000` |
| RAM | 16 GB — limit DataLoader workers to 2 |

See [MODEL_SELECTION.md](MODEL_SELECTION.md) for full tuning guide.
