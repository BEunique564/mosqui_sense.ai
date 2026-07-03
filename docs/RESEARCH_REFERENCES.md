# Research References — MosquiSense AI

Scientific and operational foundations. Japan-informed multi-source fusion is a **core design principle**, not an add-on.

---

## Japan — Primary References

### 1. SORA Technology — METI AI Outbreak Prediction Program (2025)

**Source:** [SORA Technology METI Announcement](https://sora-technology.com/news_en/notice-250108/)

**What they do:** Japanese startup (Nagoya) selected by Japan Ministry of Economy, Trade and Industry (METI) for AI-driven infectious disease outbreak prediction integrating **drone imagery, satellite data, weather, and flood simulation**.

**Applied to MosquiSense:**
- Multi-source fusion architecture (not single-model weather prediction)
- Flood/water persistence as disease risk driver
- Resource optimization for medical/vector control deployment
- METI-grade documentation and audit trail requirements

### 2. SORA Dengue Vector Control Pilot — Philippines (2025)

**Source:** [SORA Philippines Pilot](https://sora-technology.com/news_en/notice-250903/)

**What they do:** Adapted malaria control stack to **dengue** using drone surveys + AI risk mapping on Leyte Island.

**Applied to MosquiSense:**
- Dengue/Aedes focus (matches UP vector profile)
- Pre-outbreak hotspot identification before spraying
- Field GPS-guided operator workflow
- Asian urban/peri-urban context validation

### 3. SORA Health Intelligence Room — UNDP Digital X

**Source:** [UNDP Digital X — SORA](https://digitalx.undp.org/SORA_dx3.html)

**What they do:** Integrated platform: satellite + drone + climate + hydrological modeling → automated risk classification.

**Applied to MosquiSense:**
- Municipality dashboard pattern (Health Intelligence Room → our Module 11)
- Replacing manual surveillance with scalable monitoring
- Cost/insecticide reduction KPIs for government reporting

### 4. Sophia University + JAXA — Remote Sensing + AI for Dengue (2023)

**Source:** [Sophia University Press Release](https://www.sophia.ac.jp/eng/article/news/release/press20230323/)  
**Publication:** Geo-spatial Information Science (Anno et al.)

**Authors:** Sumiko Anno (Sophia Univ.), Hirakawa Tsubasa, Satoru Sugita, Shinya Yasumoto (Chubu Univ.), Yoshinobu Sasaki & Kei Oyoshi (**JAXA**)

**Findings:**
- Combined climatic remote sensing (rainfall, SST, radiation) with case geolocation for spatiotemporal dengue prediction
- Identified challenges: label imbalance, resolution limits, need for higher-resolution satellite data

**Applied to MosquiSense:**
- JAXA collaboration precedent → we use **ISRO-JAXA GSMaP_ISRO** rainfall
- Ground-truth labeling from municipal health records (not RS alone)
- TFT + CatBoost hybrid addresses their "different model architecture" recommendation
- U-Net NDWI addresses resolution gap for stagnant water

### 5. Japan Institute for Health Security — Mosquito-borne Disease Surveillance

**Source:** [NIID/JIHS Surveillance Topic](https://id-info.jihs.go.jp/en/surveillance/iasr/pathogens/vol43/508/508t.html)

**Framework:** Vector surveillance, larval source elimination, rapid information sharing prefecture ↔ national ↔ residents.

**Applied to MosquiSense:**
- Citizen alert channels aligned with Japanese "situational awareness" model
- Outbreak response sequence: detect → investigate → spray → notify

---

## India — Primary References

### 6. ISRO-JAXA GSMaP_ISRO Precipitation (MOSDAC)

**Source:** [MOSDAC GSMaP_ISRO](https://www.mosdac.gov.in/gsmap-isro-rain)  
**API:** [MOSDAC Download API Manual](https://www.mosdac.gov.in/downloadapi-manual)

**Product:** Hourly 0.1° rainfall over Indian landmass, March 2000–present. JAXA GSMaP algorithm + IMD gauge correction.

**Applied to MosquiSense:**
- Module 1 primary rainfall input
- `rain_7d_mm`, `rain_15d_mm` features
- Direct Japan-India space agency collaboration — scientific continuity

### 7. Sentinel-2 NDWI Breeding Habitat Mapping — Tiruchirappalli

**Source:** [InfoNTD — Tiruchirappalli RS/GIS Study](https://www.infontd.org/resource/identification-and-mapping-mosquito-breeding-habitats-tiruchirappalli-city-using-remote)

**Findings:** Sentinel-2 + GPS ground-truthing mapped cesspools and stagnant domestic wastewater near residential areas (Culex/Aedes breeding).

**Applied to MosquiSense:**
- Module 5 NDWI formula: `(Green − NIR) / (Green + NIR)`
- Water class taxonomy: stagnant vs temporary vs flooded
- PostGIS polygon storage for ward-level breeding score

### 8. Lucknow Municipal Corporation Context

**Vectors:** Aedes aegypti (dengue), Anopheles (malaria), Culex (filariasis/JE)  
**Seasonality:** Pre-monsoon (March–June) and post-monsoon (August–October) peaks  
**Data partners (pilot):** LMC Health Dept, UP State Malaria Officer, IMD Lucknow observatory

---

## Methodological References

| Topic | Reference | Use in MosquiSense |
|-------|-----------|-------------------|
| NDWI water index | McFeeters (1996) | Module 5 baseline index |
| Temporal Fusion Transformer | Lim et al. (2021) | 15-day forecast head |
| CatBoost | Prokhorenkova et al. (2018) | Tabular risk head |
| ST-DBSCAN | Birant & Kut (2007) | Hotspot clustering |
| Vehicle Routing | OR-Tools Google | Module 9 spray optimization |
| YOLOv11 | Ultralytics (2024) | Citizen CV pipeline |

---

## What "100% Effective" Means (Realistic Definition)

No municipal AI system achieves 100% outbreak prevention. MosquiSense targets **government-auditable effectiveness**:

| Dimension | Target | Measurement |
|-----------|--------|-------------|
| Early warning | ≥ 12 days median lead time | Backtest vs trap data |
| Resource efficiency | ≥ 25% fuel reduction | Spray logs pre/post |
| Citizen reach | ≥ 80% alert delivery | Notification delivery reports |
| False alarm control | Precision@20 wards ≥ 0.70 | Outbreak confirmation |
| Uptime | 99.5% monsoon season | Prometheus SLA |

Continuous improvement via Japan-style **feedback loops** (SORA Health Intelligence Room pattern) and weekly CatBoost incremental retraining.

---

## Data Ethics & Compliance

- **Digital Personal Data Protection Act, 2023 (India)** — citizen consent, photo anonymization
- **National Malaria Control Programme** reporting alignment
- **Geo-spatial Guidelines, 2021** — restricted zone handling for defence areas near Lucknow AFS

---

## Future Research Integration (Phase 4+)

- **ST-GNN** — when UP-wide ward adjacency graph matures (cite Yu et al. spatio-temporal GNN surveys)
- **JAXA GPM / AMSR2** — additional MOSDAC products for cloud-penetrating rainfall
- **Drone surveys** — SORA-style aerial validation for ward-level ground truthing (optional Module 1b)
