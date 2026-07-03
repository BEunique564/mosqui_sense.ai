"""
CatBoost training — Module 7 tabular head.
Optimized for CPU + incremental retraining on RTX 3050 dev machine.
"""

import argparse
from pathlib import Path

import mlflow
import pandas as pd
from catboost import CatBoostClassifier, Pool


def train(
    features_path: Path,
    model_out: Path,
    incremental_model: Path | None = None,
    iterations: int = 2000,
):
    df = pd.read_parquet(features_path)
    feature_cols = [c for c in df.columns if c not in ("ward_id", "date", "outbreak_label")]
    cat_features = ["ward_id"] if "ward_id" in feature_cols else []

    X = df[feature_cols]
    y = df["outbreak_label"]

    split = int(len(df) * 0.8)
    train_pool = Pool(X.iloc[:split], y.iloc[:split], cat_features=cat_features)
    eval_pool = Pool(X.iloc[split:], y.iloc[split:], cat_features=cat_features)

    init_model = None
    if incremental_model and incremental_model.exists():
        init_model = CatBoostClassifier()
        init_model.load_model(str(incremental_model))

    model = CatBoostClassifier(
        iterations=iterations,
        depth=8,
        learning_rate=0.05,
        loss_function="Logloss",
        auto_class_weights="Balanced",
        task_type="CPU",
        verbose=100,
    )

    mlflow.set_experiment("mosquisense-catboost")
    with mlflow.start_run():
        if init_model:
            model.fit(train_pool, eval_set=eval_pool, init_model=init_model)
        else:
            model.fit(train_pool, eval_set=eval_pool)

        model_out.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(str(model_out))
        mlflow.log_artifact(str(model_out))
        mlflow.log_param("iterations", iterations)
        print(f"Model saved to {model_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", default="data/processed/features.parquet")
    parser.add_argument("--output", default="models/catboost/latest.cbm")
    parser.add_argument("--incremental", default=None)
    parser.add_argument("--iterations", type=int, default=2000)
    args = parser.parse_args()
    train(
        Path(args.features),
        Path(args.output),
        Path(args.incremental) if args.incremental else None,
        args.iterations,
    )
