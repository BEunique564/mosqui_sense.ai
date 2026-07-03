# Model Selection & Comparison — MosquiSense AI

## Executive Recommendation

**Production stack: Hybrid Ensemble**

```
Final Risk Score = 0.40 × CatBoost + 0.35 × TFT + 0.25 × NDWI_Water_Index
```

**Primary production model for 15-day outbreak prediction:** **Temporal Fusion Transformer (TFT)** fused with **CatBoost** tabular scoring.

**Why not a single model?** Mosquito ecology combines slow climatic drivers (15-day horizon), heterogeneous municipal records (spray gaps, complaints), and spatial water persistence (NDWI). No single architecture captures all three signal types optimally — validated by Sophia/JAXA dengue research and SORA Technology's multi-source fusion approach in Japan.

---

## Full Model Comparison

### Gradient Boosting (Tabular)

| Model | Selected? | Pros | Cons | MosquiSense Fit |
|-------|-----------|------|------|-----------------|
| **CatBoost** | ✅ **YES** | Native categorical (ward, chemical type), ordered boosting, fast CPU inference, incremental training | Weak pure time-series | **Best for ward-level risk from spray/complaint/drain features** |
| XGBoost | ⚪ Backup | Mature, GPU hist mode | Manual categorical encoding | Good fallback; CatBoost wins on municipal categoricals |
| LightGBM | ⚪ Backup | Fast on large data | Sensitive to overfitting on sparse wards | Use at national scale if >1M rows/day |
| Random Forest | ❌ No | Interpretable | Lower accuracy vs boosting | Superseded for production |

### Deep Learning — Time Series

| Model | Selected? | Pros | Cons | MosquiSense Fit |
|-------|-----------|------|------|-----------------|
| **TFT** | ✅ **YES** | Multi-horizon (15-day), variable selection, attention interpretability | GPU memory | **Primary forecast head** |
| LSTM | ❌ No | Simple | Vanishing gradients, single horizon | Superseded by TFT |
| Informer | ⚪ Research | Long sequence efficiency | Complex tuning | Consider at national scale (>2yr history) |
| PatchTST | ⚪ Research | SOTA on benchmarks | Less interpretability for govt audits | Phase 4 evaluation |
| N-BEATS | ❌ No | Univariate focus | Poor multi-variate weather fusion | Not suitable |
| Prophet | ⚪ Baseline | Easy seasonality | Fails on exogenous spikes (monsoon) | KPI baseline only |
| ARIMA | ⚪ Baseline | Classical | Cannot ingest NDWI/complaints | Legacy comparison metric |

### Graph Neural Networks

| Model | Selected? | Pros | Cons | MosquiSense Fit |
|-------|-----------|------|------|-----------------|
| ST-GNN | ⚪ Phase 4 | Models ward adjacency diffusion | Needs large graph, heavy GPU | Deploy when UP-wide graph stable |
| Standard GNN | ❌ MVP | Spatial structure | No temporal head alone | Combine with TFT later |

**MVP approach:** ST-DBSCAN hotspot clustering + CatBoost spatial lag features (`neighbor_mean_risk_7d`). Upgrade to ST-GNN at state scale.

### Computer Vision

| Model | Selected? | Pros | Cons | MosquiSense Fit |
|-------|-----------|------|------|-----------------|
| **YOLOv11n** | ✅ **YES** | Fast, RTX 3050 friendly, waterlogging/garbage/drain classes | Needs labeled India data | **Citizen photo pipeline** |
| RT-DETR | ⚪ Alt | Transformer detector | Heavier than YOLO11n | If accuracy gap >5% mAP |
| SAM2 | ⚪ Segmentation | Precise masks | Too slow for mobile edge | Post-process water polygons only |
| GroundingDINO | ⚪ Zero-shot | Open vocabulary | Unreliable for drain severity | Prototype tool for analysts |

### Satellite Water Detection

| Model | Selected? | Pros | Cons | MosquiSense Fit |
|-------|-----------|------|------|-----------------|
| **U-Net + NDWI** | ✅ **YES** | Physics-informed (NDWI formula), Sentinel-2 proven in Tiruchirappalli | Cloud cover gaps | **Module 5 core** |
| NDWI alone | ⚪ Feature | Simple index | No stagnation classification | Input to U-Net |

### Optimization

| Model | Selected? | Pros | Cons | MosquiSense Fit |
|-------|-----------|------|------|-----------------|
| **Google OR-Tools VRP** | ✅ **YES** | Industry standard, auditable routes | Needs good risk input | **Module 9 core** |
| RL (PPO) | ⚪ Phase 3 | Adaptive to traffic | Hard to audit for government | Hybrid: OR-Tools primary, RL fine-tune |

---

## Production Model: Detailed Specification

### Head 1 — Temporal Fusion Transformer

```yaml
model: TemporalFusionTransformer
params:
  hidden_size: 64          # RTX 3050 constraint
  attention_head_size: 4
  dropout: 0.1
  hidden_continuous_size: 16
  loss: QuantileLoss([0.1, 0.5, 0.9])
  max_encoder_length: 60   # 60 days history
  max_prediction_length: 15
  learning_rate: 0.001
  batch_size: 32
  precision: fp16          # mixed precision
```

**Inputs:** daily ward features — rainfall, humidity, LST, NDWI mean, complaint count, spray gap  
**Output:** P(outbreak) at horizons t+1…t+15

### Head 2 — CatBoost Classifier

```yaml
model: CatBoostClassifier
params:
  iterations: 2000
  depth: 8
  learning_rate: 0.05
  cat_features: [ward_id, chemical_type, machine_type, season]
  loss_function: Logloss
  auto_class_weights: Balanced
  task_type: CPU
  allow_writing_files: false
```

**Inputs:** engineered tabular features (see ML_PIPELINE.md)  
**Output:** risk probability → calibrated to 0-100

### Head 3 — NDWI Water Persistence Index

```
WPI = mean(NDWI) × persistence_days × stagnation_class_weight
```

Stagnation classes from U-Net: No Water (0), Moving (0.2), Temporary (0.5), Stagnant (1.0), Flooded (0.8).

### Ensemble Calibration

Platt scaling on validation set (last monsoon season). SHAP values exported for municipal audit PDFs.

---

## RTX 3050 Training Profile (4 GB VRAM, 16 GB RAM)

| Model | Batch Size | Mixed Precision | Epochs | Est. Time |
|-------|------------|-----------------|--------|-----------|
| TFT | 32 | FP16 (`amp`) | 50 | ~4 hr (110 wards) |
| U-Net | 8 | FP16 | 100 | ~6 hr |
| YOLOv11n | 16 | FP16 | 150 | ~3 hr |
| CatBoost | N/A (CPU) | — | 2000 iter | ~20 min |

**Memory tips:**
- Gradient accumulation steps=2 if OOM on TFT
- `pin_memory=False` on 16 GB RAM systems
- Tile Sentinel rasters to 512×512 before U-Net
- Use `yolo11n.pt` not `yolo11m` — m variant OOMs at batch 16

---

## Incremental & Online Learning

| Model | Incremental | Online | Strategy |
|-------|-------------|--------|----------|
| CatBoost | ✅ `init_model` | ✅ Weekly warm-start | New spray + complaint rows |
| TFT | ⚪ Fine-tune | ⚪ Monthly | Last 60 days window fine-tune 5 epochs |
| U-Net | ❌ Full retrain | ❌ Monthly | New Sentinel labels |
| YOLOv11 | ✅ Resume | ⚪ Weekly | Citizen photo active learning queue |
| Ensemble weights | ✅ | ✅ | Bayesian update on validation F1 |

**MLflow registry stages:** `None → Staging → Production → Archived`

---

## Expected KPI Targets (Lucknow Pilot)

| Metric | Target | Notes |
|--------|--------|-------|
| ROC-AUC (15-day) | ≥ 0.82 | Monsoon validation set |
| Precision @ top 20 wards | ≥ 0.70 | Resource-constrained spraying |
| Recall @ outbreak | ≥ 0.85 | Public health priority |
| F1 | ≥ 0.75 | Balanced |
| RMSE (risk score) | ≤ 12 | vs held-out entomology traps |
| Inference latency | < 200 ms/ward | CatBoost + TFT batch |
| VRP solve time | < 30 s/zone | OR-Tools 50 nodes |

---

## Japan-Informed Design Decisions

| Source | Lesson Applied |
|--------|----------------|
| SORA Technology (METI program) | Fuse satellite + weather + hydrology — not weather alone |
| Sophia Univ + JAXA (Geo-spatial Information Science) | Remote sensing labels need ground truth — we use municipal traps + citizen reports |
| SORA Philippines dengue pilot (2025) | Pre-outbreak hotspot mapping before spray deployment |
| GSMaP_ISRO (ISRO-JAXA) | Hourly rainfall product as primary MOSDAC input |

Full citations: [RESEARCH_REFERENCES.md](RESEARCH_REFERENCES.md)

---

## Inference Pipeline (Production)

```python
# Pseudocode — prediction-service
features = feature_store.get_online(ward_id, as_of=today)
tft_forecast = tft_model.predict(features, horizon=15)
catboost_risk = catboost_model.predict_proba(features_tabular)
ndwi_score = ndwi_index.get(ward_id)
risk_0_100 = ensemble(tft_forecast, catboost_risk, ndwi_score)
explain = shap_explainer(catboost_model, features_tabular)
persist(ward_id, risk_0_100, tft_forecast, explain)
```

---

## Model NOT Selected — Summary

| Model | Reason |
|-------|--------|
| Random Forest | Lower accuracy than CatBoost on same features |
| LSTM | TFT supersedes for multi-horizon |
| Prophet/ARIMA | Cannot ingest spatial NDWI + complaints |
| GNN (MVP) | Insufficient graph data at 1-ward start |
| SAM2 (primary) | Latency incompatible with citizen mobile upload |
| RL-only routing | Government audit requires deterministic OR-Tools routes |
