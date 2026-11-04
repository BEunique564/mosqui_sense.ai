# MosquiSense AI

**Production-ready mosquito outbreak prediction platform for Indian smart cities.**

> ⚠️ **Research Integrity Notice:** This README distinguishes between **IMPLEMENTED** (working code in repository), **IN PROGRESS** (development ongoing), and **PROPOSED** (to be developed under ICMR First in the World Challenge 2026 funding). The "15-day outbreak prediction" claim is a **development target**, not a validated result. No field data, no trained models, and no performance results currently exist in this repository.

---

## Project Status at a Glance

| Component | Status | Evidence / Notes |
|-----------|--------|------------------|
| System Architecture & Design | IMPLEMENTED | `docs/ARCHITECTURE.md`, `docs/DATABASE_SCHEMA.md` |
| Backend (FastAPI, PostgreSQL/PostGIS, TimescaleDB, Redis) | IMPLEMENTED | `backend/` directory |
| Database & API Schema | IMPLEMENTED | `backend/database.py`, `docs/DATABASE_SCHEMA.md` |
| CatBoost Training Script | IMPLEMENTED | `training/train_catboost.py` |
| TFT (Temporal Fusion Transformer) | PROPOSED | Referenced in docs; **no code in repository** |
| U-Net + NDWI Water Detection | PROPOSED | Referenced in docs; **no code in repository** |
| YOLOv11n Citizen Photo Pipeline | PROPOSED | Referenced in docs; **no code in repository** |
| OR-Tools VRP Spray Optimization | PROPOSED | Referenced in docs; **no code in repository** |
| Citizen Mobile App / PWA | PROPOSED | Referenced in docs; **no code in repository** |
| Municipal Partnership (LMC Lucknow) | PROPOSED | No MoU or data-sharing agreement in evidence |
| ICMR FiW 2026 Field Validation | PROPOSED | To be conducted if funded |
| 15-Day Outbreak Prediction Performance | **NOT VALIDATED** | Repository metrics (ROC-AUC ≥ 0.82, etc.) are **targets only** |

---

## Project Overview

Predict mosquito outbreak probability. Optimize spraying schedules, manpower, fuel, chemicals, and emergency response while notifying citizens in real time.

**Important:** The 15-day advance prediction is a research hypothesis under ICMR First in the World Challenge 2026. It is **not yet validated** against entomological ground truth.

| Scope | Geography |
|-------|-----------|
| Phase 1 (MVP / PoC) | 1 ward, Lucknow |
| Phase 2 (Pilot) | 10 wards, Lucknow |
| Phase 3 (Production) | Full Lucknow Municipal Corporation |
| Phase 4 (State) | Entire Uttar Pradesh |
| Phase 5 (National) | Pan-India |

---

## Architecture Summary

```
Satellite (MOSDAC) ──┐
Weather API ─────────┼──► Feature Store ──► Hybrid AI ──► Dashboard + Alerts
Municipality DB ─────┤         ▲                              │
Citizen Reports ─────┘         └── Feedback Loop ── Retraining ─┘
NDWI / CV Pipeline ────┘
```

## Production Model Stack (Planned vs Implemented)

| Task | Model | Status | Why |
|------|-------|--------|-----|
| 15-day outbreak forecast | Temporal Fusion Transformer (TFT) | **PROPOSED** | Multi-horizon, interpretable attention |
| Ward risk scoring | CatBoost | **IMPLEMENTED** | Tabular + categorical, fast CPU inference |
| Stagnant water (satellite) | U-Net + NDWI | **PROPOSED** | Physics-informed segmentation |
| Citizen photo analysis | YOLOv11n | **PROPOSED** | Real-time on edge devices |
| Spray route optimization | Google OR-Tools VRP | **PROPOSED** | Proven municipal routing |
| Final risk fusion | Weighted ensemble | **PROPOSED** | Robust, auditable for government |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js & npm
- RTX 3050 (recommended for GPU training, 4 GB VRAM)

### 1. Infrastructure
```bash
docker compose -f deployment/docker-compose.yml up -d
```

### 2. Backend
```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

> **Note:** Commands are as per README. Actual success depends on repository configuration, dependencies, and environment variables (`.env.example`).

---

## Documentation

| Document | Description | Status |
|----------|-------------|--------|
| [Architecture](docs/ARCHITECTURE.md) | System design, microservices, diagrams | IMPLEMENTED (design only) |
| [Model Selection](docs/MODEL_SELECTION.md) | Full model comparison + RTX 3050 tuning | PROPOSED (TFT/U-Net/YOLO not coded) |
| [Database Schema](docs/DATABASE_SCHEMA.md) | PostgreSQL/PostGIS ER diagram | IMPLEMENTED |
| [API Design](docs/API_DESIGN.md) | REST endpoints, auth, webhooks | IMPLEMENTED (design) |
| [ML Pipeline](docs/ML_PIPELINE.md) | Training, validation, retraining | PROPOSED (not executed on real data) |
| [Deployment](docs/DEPLOYMENT.md) | Docker, K8s, Lucknow rollout | PROPOSED |
| [Roadmap](docs/ROADMAP.md) | 5-phase timeline with milestones | PROPOSED |
| [Research References](docs/RESEARCH_REFERENCES.md) | Japan, ISRO-JAXA, India studies | NEEDS VERIFICATION |
| [Testing Strategy](docs/TESTING_STRATEGY.md) | Unit, integration, ML validation | PROPOSED |
| [Notification Workflow](docs/NOTIFICATION_WORKFLOW.md) | SMS, WhatsApp, push, IVR | PROPOSED |

---

## Research Foundation

Built on validated approaches from:

- **Japan (SORA Technology / METI)** — satellite + weather + hydrology fusion for vector control
- **JAXA + Sophia University** — remote sensing + ML for spatiotemporal dengue prediction
- **ISRO-JAXA GSMaP_ISRO** — hourly 0.1° rainfall over India (MOSDAC)
- **India (Tiruchirappalli)** — Sentinel-2 NDWI breeding habitat mapping

**Verification status:** All external references cited above require primary-source confirmation before citation in an ICMR proposal.

---

## License

Proprietary — @BEunique564

---

## ICMR First in the World Challenge 2026 — Important

This repository is at **Proof of Concept (PoC) stage**. No models have been trained on field data. No forecasts have been validated. No institutional partnership with Lucknow Municipal Corporation or NCVBDC exists. All performance metrics in documentation are **development targets**, not achieved results. ICMR funding is requested to move from PROPOSED to IMPLEMENTED status for TFT, U-Net, YOLO, and field validation components.
