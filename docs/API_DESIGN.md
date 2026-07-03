# API Design — MosquiSense AI

Base URL: `https://api.mosquisense.in/v1`  
Auth: Bearer JWT (RS256). Citizen endpoints also accept API key + OTP.

OpenAPI spec: `backend/app/openapi.yaml`

---

## Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | POST | Email/password → access + refresh tokens |
| `/auth/otp/send` | POST | Citizen phone OTP (NIC SMS gateway) |
| `/auth/otp/verify` | POST | Verify OTP → citizen JWT |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/mfa/verify` | POST | TOTP for admin roles |

**Roles (RBAC):** `super_admin`, `state_admin`, `municipal_officer`, `field_operator`, `analyst`, `citizen`

---

## Predictions & Risk

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/predictions/wards/{ward_id}` | GET | officer+ | Current risk score + 15-day forecast |
| `/predictions/wards` | GET | officer+ | Paginated ward list with risk (filter by district) |
| `/predictions/heatmap` | GET | officer+ | GeoJSON risk polygons or MVT tiles |
| `/predictions/hotspots` | GET | officer+ | Active ST-DBSCAN clusters |
| `/predictions/explain/{ward_id}` | GET | analyst+ | SHAP feature contributions |
| `/predictions/trigger` | POST | admin | Manual inference run (async Celery) |

**Response example — `/predictions/wards/{ward_id}`:**

```json
{
  "ward_id": "uuid",
  "ward_code": "LKO-042",
  "risk_score": 78.4,
  "outbreak_probability_15d": 0.71,
  "horizon": [
    {"day": 1, "probability": 0.32},
    {"day": 15, "probability": 0.71}
  ],
  "model_version": "ensemble-v2.3.1",
  "predicted_at": "2026-07-03T06:00:00+05:30",
  "top_drivers": [
    {"feature": "rain_15d_mm", "impact": 0.18},
    {"feature": "spray_gap_days", "impact": 0.14},
    {"feature": "ndwi_stagnant_pct", "impact": 0.12}
  ]
}
```

---

## GIS & Maps

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/gis/wards` | GET | officer+ | Ward boundaries GeoJSON |
| `/gis/water-bodies` | GET | officer+ | NDWI polygons by class |
| `/gis/spray-routes/{event_id}` | GET | officer+ | Historical route GeoJSON |
| `/gis/layers` | GET | officer+ | GeoServer layer catalog |
| `/gis/tiles/{layer}/{z}/{x}/{y}` | GET | officer+ | Cached map tiles |

---

## Municipality Operations

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/spray/events` | GET/POST | operator+ | List/create spray records |
| `/spray/events/{id}` | GET/PATCH | operator+ | Single event CRUD |
| `/spray/optimize` | POST | officer+ | OR-Tools VRP for ward list |
| `/complaints` | GET/POST | officer+ | Municipal complaint registry |
| `/analytics/fuel-savings` | GET | officer+ | Fuel/chemical cost analysis |
| `/analytics/kpi` | GET | analyst+ | Model + operational KPIs |

**POST `/spray/optimize` body:**

```json
{
  "ward_ids": ["uuid1", "uuid2"],
  "vehicles": [{"id": "v1", "capacity_liters": 200, "fuel_tank": 50}],
  "workers_available": 12,
  "depot_location": [26.8467, 80.9462],
  "max_route_hours": 8
}
```

---

## Citizen Reporting

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/citizen/reports` | POST | citizen | Submit report with photo + GPS |
| `/citizen/reports/mine` | GET | citizen | User's report history |
| `/citizen/alerts/subscribe` | POST | citizen | Opt-in to ward alerts |
| `/citizen/alerts/nearby` | GET | citizen | Active hotspots near location |
| `/citizen/spray-schedule` | GET | citizen | Upcoming spray in ward |

**POST `/citizen/reports` (multipart):**

```
report_type: mosquito | water_logging | drain | garbage
latitude, longitude, severity (1-5), mosquito_density (1-5), photo (file)
```

---

## Notifications

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/notifications/send` | POST | admin | Broadcast alert to ward/region |
| `/notifications/templates` | GET | admin | SMS/WhatsApp templates |
| `/notifications/history` | GET | officer+ | Delivery status log |
| `/webhooks/delivery-status` | POST | system | SMS/WhatsApp delivery callbacks |

---

## Satellite & Weather (Internal)

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/internal/satellite/sync` | POST | system | Trigger MOSDAC download |
| `/internal/weather/sync` | POST | system | Trigger forecast ingest |
| `/internal/ndwi/process` | POST | system | Sentinel NDWI job |

Protected by service-to-service mTLS + `X-Service-Key`.

---

## WebSocket

`wss://api.mosquisense.in/v1/ws/dashboard`

| Event | Payload |
|-------|---------|
| `risk.updated` | `{ward_id, risk_score, predicted_at}` |
| `hotspot.new` | `{hotspot_id, geom, severity}` |
| `spray.completed` | `{event_id, ward_id, fuel_liters}` |

---

## Rate Limits

| Tier | Limit |
|------|-------|
| Citizen | 60 req/min |
| Officer | 300 req/min |
| Internal | 1000 req/min |

---

## Error Format

```json
{
  "error": {
    "code": "WARD_NOT_FOUND",
    "message": "Ward LKO-999 not in scope",
    "request_id": "req_abc123"
  }
}
```

HTTP codes: 400 validation, 401 auth, 403 RBAC, 404 not found, 429 rate limit, 503 ML service unavailable.

---

## Versioning

URL prefix `/v1`. Breaking changes → `/v2` with 12-month deprecation window (government SLA).
