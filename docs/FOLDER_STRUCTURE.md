# MosquiSense AI — Enterprise Project Structure

```
mosquisense/
├── README.md
├── .env.example
├── .gitignore
│
├── docs/                          # Architecture & government deliverables
│   ├── ARCHITECTURE.md
│   ├── MODEL_SELECTION.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_DESIGN.md
│   ├── ML_PIPELINE.md
│   ├── DEPLOYMENT.md
│   ├── ROADMAP.md
│   ├── RESEARCH_REFERENCES.md
│   ├── NOTIFICATION_WORKFLOW.md
│   └── TESTING_STRATEGY.md
│
├── backend/                       # FastAPI microservices (Module 7, 9, 11 API)
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                  # Config, security, DB session
│   │   ├── domain/                # Entities (Ward, RiskScore, SprayEvent)
│   │   ├── application/           # Use cases (Clean Architecture)
│   │   ├── infrastructure/        # Repositories, external APIs
│   │   ├── services/
│   │   │   ├── prediction/        # TFT, CatBoost, ensemble
│   │   │   └── optimization/      # OR-Tools VRP
│   │   ├── api/v1/endpoints/
│   │   └── workers/               # Celery tasks
│   └── tests/
│
├── frontend/                      # Next.js dashboard (Module 11)
│   ├── package.json
│   └── src/app/
│
├── models/                        # Trained model artifacts (DVC tracked)
│   ├── catboost/
│   ├── tft/
│   ├── unet/
│   └── yolo/
│
├── training/                      # ML training pipeline
│   ├── feature_engineering/
│   ├── train_catboost.py
│   ├── train_tft.py
│   ├── train_unet.py
│   ├── train_yolo.py
│   ├── calibrate_ensemble.py
│   ├── validate_backtest.py
│   ├── dvc.yaml
│   └── configs/
│
├── satellite/                     # Module 1 + Module 5
│   ├── collector/                 # MOSDAC GSMaP_ISRO
│   └── ndwi/                      # Sentinel NDWI + U-Net
│
├── gis/                           # Module 6
│   ├── geoserver/                 # Layer styles, SLD
│   ├── qgis/                      # Offline projects
│   └── scripts/                   # Shapefile import, ST-DBSCAN
│
├── notifications/                 # Module 10
│   ├── channels/                  # SMS, WhatsApp, FCM, IVR
│   ├── rules/
│   └── templates/
│
├── database/                      # PostgreSQL + PostGIS
│   ├── init/
│   ├── migrations/                # Alembic
│   └── seeds/                     # Lucknow wards
│
├── deployment/                    # Docker, K8s, Helm
│   ├── docker-compose.yml
│   ├── kubernetes/
│   ├── helm/
│   └── load/                      # k6 scripts
│
└── .github/workflows/             # CI/CD + ML validation gates
```

## Module → Directory Mapping

| Module | Directory |
|--------|-----------|
| 1 MOSDAC Collector | `satellite/collector/` |
| 2 Weather API | `backend/app/workers/weather_sync.py` |
| 3 Municipality DB | `database/` |
| 4 Citizen Reporting | `backend/app/api/v1/endpoints/citizen.py`, `frontend/` |
| 5 NDWI Water Detection | `satellite/ndwi/` |
| 6 GIS Engine | `gis/`, PostGIS in `database/` |
| 7 Mosquito Prediction AI | `training/`, `backend/app/services/prediction/` |
| 8 Computer Vision | `training/train_yolo.py`, CV worker |
| 9 Resource Optimization | `backend/app/services/optimization/` |
| 10 Citizen Notification | `notifications/` |
| 11 Municipality Dashboard | `frontend/` |
| 12 Analytics | `backend/app/api/v1/endpoints/analytics.py` |
