# MosquiSense AI

**Production-ready mosquito outbreak prediction platform for Indian smart cities.**

Predict mosquito outbreak probability **15 days before** it occurs. Optimize spraying schedules, manpower, fuel, chemicals, and emergency response while notifying citizens in real time.

| Scope | Geography |
|-------|-----------|
| Phase 1 (MVP) | 1 ward, Lucknow |
| Phase 2 (Pilot) | 10 wards, Lucknow |
| Phase 3 (Production) | Full Lucknow Municipal Corporation |
| Phase 4 (State) | Entire Uttar Pradesh |
| Phase 5 (National) | Pan-India |

## Architecture Summary

```
Satellite (MOSDAC) ──┐
Weather API ─────────┼──► Feature Store ──► Hybrid AI ──► Dashboard + Alerts
Municipality DB ─────┤         ▲                              │
Citizen Reports ─────┘         └── Feedback Loop ── Retraining ─┘
NDWI / CV Pipeline ────┘
```

## Production Model Stack (RTX 3050 Optimized)

| Task | Model | Why |
|------|-------|-----|
| 15-day outbreak forecast | **Temporal Fusion Transformer (TFT)** | Multi-horizon, interpretable attention |
| Ward risk scoring | **CatBoost** | Tabular + categorical, fast CPU inference |
| Stagnant water (satellite) | **U-Net + NDWI** | Physics-informed segmentation |
| Citizen photo analysis | **YOLOv11n** | Real-time on 4 GB VRAM |
| Spray route optimization | **Google OR-Tools VRP** | Proven municipal routing |
| Final risk fusion | **Weighted ensemble** | Robust, auditable for government |

## Quick Start

```bash
# Infrastructure
docker compose -f deployment/docker-compose.yml up -d

# Backend
cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design, microservices, diagrams |
| [Model Selection](docs/MODEL_SELECTION.md) | Full model comparison + RTX 3050 tuning |
| [Database Schema](docs/DATABASE_SCHEMA.md) | PostgreSQL/PostGIS ER diagram |
| [API Design](docs/API_DESIGN.md) | REST endpoints, auth, webhooks |
| [ML Pipeline](docs/ML_PIPELINE.md) | Training, validation, retraining |
| [Deployment](docs/DEPLOYMENT.md) | Docker, K8s, Lucknow rollout |
| [Roadmap](docs/ROADMAP.md) | 5-phase timeline with milestones |
| [Research References](docs/RESEARCH_REFERENCES.md) | Japan, ISRO-JAXA, India studies |
| [Testing Strategy](docs/TESTING_STRATEGY.md) | Unit, integration, ML validation |
| [Notification Workflow](docs/NOTIFICATION_WORKFLOW.md) | SMS, WhatsApp, push, IVR |

## Research Foundation

Built on validated approaches from:

- **Japan (SORA Technology / METI)** — satellite + weather + hydrology fusion for vector control
- **JAXA + Sophia University** — remote sensing + ML for spatiotemporal dengue prediction
- **ISRO-JAXA GSMaP_ISRO** — hourly 0.1° rainfall over India (MOSDAC)
- **India (Tiruchirappalli)** — Sentinel-2 NDWI breeding habitat mapping

See [docs/RESEARCH_REFERENCES.md](docs/RESEARCH_REFERENCES.md) for full citations.

## License

Proprietary — Lucknow Municipal Corporation / Government of Uttar Pradesh deployment license required.
