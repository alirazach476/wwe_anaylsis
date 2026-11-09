"""ML experiments on PLE marts — booking-pattern / estimation, not athletic prediction.

Experiments:
1. Wrestler performance clustering (KMeans)
2. Match duration regression (RandomForest)
3. Attendance estimation (RandomForest) with time-aware split
4. Career segmentation (hierarchical-style via Agglomerative on sample)
5. Similar-event recommendation (nearest neighbors on event features)
6. Title-match classification (booking pattern)

Avoid leakage: attendance model uses year/series/country only (pre-event features).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "data" / "warehouse" / "marts"
MODELS = ROOT / "models"
MODELS.mkdir(parents=True, exist_ok=True)


def _rmse(y_true, y_pred) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def wrestler_clustering() -> dict:
    df = pd.read_csv(MARTS / "mart_wrestler_performance.csv")
    feats = df[["matches", "wins", "losses", "title_matches", "main_events"]].fillna(0)
    # filter low sample
    mask = feats["matches"] >= 5
    X = StandardScaler().fit_transform(feats.loc[mask])
    km = KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    sil = float(silhouette_score(X, labels)) if len(X) > 10 else None
    out = df.loc[mask].copy()
    out["cluster"] = labels
    out.to_csv(MODELS / "wrestler_clusters.csv", index=False)
    return {"experiment": "wrestler_kmeans", "silhouette": sil, "n": int(mask.sum()), "k": 4}


def duration_regression() -> dict:
    df = pd.read_csv(MARTS / "mart_match_analytics.csv")
    df = df.dropna(subset=["match_duration_seconds"])
    df["is_title"] = df["is_title_match"].astype(str).str.lower().isin(["true", "1"]).astype(int)
    df["is_main"] = df["is_main_event"].astype(str).str.lower().isin(["true", "1"]).astype(int)
    le = LabelEncoder()
    df["type_enc"] = le.fit_transform(df["match_type_group"].fillna("other"))
    # time-aware: train on years < 2020, test >= 2020
    train = df[df["event_year"] < 2020]
    test = df[df["event_year"] >= 2020]
    if len(train) < 50 or len(test) < 20:
        train, test = train_test_split(df, test_size=0.25, random_state=42)
    feats = ["type_enc", "is_title", "is_main", "event_year"]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(train[feats], train["match_duration_seconds"])
    pred = model.predict(test[feats])
    return {
        "experiment": "duration_rf",
        "mae": float(mean_absolute_error(test["match_duration_seconds"], pred)),
        "rmse": _rmse(test["match_duration_seconds"], pred),
        "r2": float(r2_score(test["match_duration_seconds"], pred)),
        "n_train": len(train),
        "n_test": len(test),
        "feature_importance": dict(zip(feats, map(float, model.feature_importances_))),
        "disclaimer": "Duration estimation from stipulation features; not causal.",
    }


def attendance_estimation() -> dict:
    df = pd.read_csv(MARTS / "mart_attendance_analytics.csv")
    df = df.dropna(subset=["attendance"])
    df["series_enc"] = LabelEncoder().fit_transform(df["event_series"].fillna("Unknown"))
    df["country_enc"] = LabelEncoder().fit_transform(df["country_name"].fillna("Unknown"))
    train = df[df["event_year"] < 2018]
    test = df[df["event_year"] >= 2018]
    if len(train) < 30 or len(test) < 10:
        train, test = train_test_split(df, test_size=0.25, random_state=42)
    feats = ["event_year", "series_enc", "country_enc"]
    model = RandomForestRegressor(n_estimators=120, random_state=42)
    model.fit(train[feats], train["attendance"])
    pred = model.predict(test[feats])
    return {
        "experiment": "attendance_rf",
        "mae": float(mean_absolute_error(test["attendance"], pred)),
        "rmse": _rmse(test["attendance"], pred),
        "r2": float(r2_score(test["attendance"], pred)),
        "n_train": len(train),
        "n_test": len(test),
        "feature_importance": dict(zip(feats, map(float, model.feature_importances_))),
        "disclaimer": "Uses pre-event features only (year/series/country).",
    }


def career_segmentation() -> dict:
    df = pd.read_csv(MARTS / "mart_wrestler_performance.csv")
    feats = df[["matches", "win_pct", "title_matches", "career_span_years"]].copy()
    feats["win_pct"] = feats["win_pct"].fillna(0)
    feats = feats.fillna(0)
    mask = df["matches"] >= 8
    X = StandardScaler().fit_transform(feats.loc[mask])
    # sample for hierarchical cost
    if len(X) > 400:
        idx = np.random.RandomState(42).choice(len(X), 400, replace=False)
        Xs = X[idx]
    else:
        Xs = X
        idx = np.arange(len(X))
    model = AgglomerativeClustering(n_clusters=5)
    labels = model.fit_predict(Xs)
    sil = float(silhouette_score(Xs, labels))
    return {
        "experiment": "career_agglomerative",
        "silhouette": sil,
        "k": 5,
        "n": int(len(Xs)),
    }


def similar_events() -> dict:
    df = pd.read_csv(MARTS / "mart_event_analytics.csv")
    df["series_enc"] = LabelEncoder().fit_transform(df["event_series"].fillna("Unknown"))
    feats = df[["event_year", "series_enc", "matches", "title_matches"]].fillna(0)
    X = StandardScaler().fit_transform(feats)
    nn = NearestNeighbors(n_neighbors=6)
    nn.fit(X)
    distances, indices = nn.kneighbors(X[:20])
    rows = []
    for i, neigh in enumerate(indices):
        for j, d in zip(neigh[1:], distances[i][1:]):
            rows.append(
                {
                    "event": df.iloc[i]["event_name"],
                    "similar": df.iloc[j]["event_name"],
                    "distance": float(d),
                }
            )
    pd.DataFrame(rows).to_csv(MODELS / "similar_events_sample.csv", index=False)
    return {"experiment": "similar_events_nn", "n_seed": 20, "neighbors": 5}


def title_match_classification() -> dict:
    df = pd.read_csv(MARTS / "mart_match_analytics.csv")
    y = df["is_title_match"].astype(str).str.lower().isin(["true", "1"]).astype(int)
    df["type_enc"] = LabelEncoder().fit_transform(df["match_type_group"].fillna("other"))
    df["is_main"] = df["is_main_event"].astype(str).str.lower().isin(["true", "1"]).astype(int)
    X = df[["type_enc", "is_main", "event_year"]].fillna(0)
    # booking-pattern exploration
    train = df["event_year"] < 2020
    if train.sum() < 50 or (~train).sum() < 20:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    else:
        X_train, y_train = X[train], y[train]
        X_test, y_test = X[~train], y[~train]
    clf = GradientBoostingClassifier(random_state=42)
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)
    return {
        "experiment": "title_match_gb",
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "disclaimer": "Historical booking-pattern classification; results are scripted entertainment.",
    }


def main() -> None:
    registry = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "disclaimer": "WWE outcomes are scripted. Models explore historical booking patterns / estimation only.",
        "experiments": [],
    }
    for fn in (
        wrestler_clustering,
        duration_regression,
        attendance_estimation,
        career_segmentation,
        similar_events,
        title_match_classification,
    ):
        result = fn()
        registry["experiments"].append(result)
        print(result["experiment"], {k: v for k, v in result.items() if k != "feature_importance"})
    (MODELS / "registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"Registry → {MODELS / 'registry.json'}")


if __name__ == "__main__":
    main()
