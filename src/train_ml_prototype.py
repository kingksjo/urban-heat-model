"""Train and evaluate Phase 4 Urban Heat Pattern Explorer ML models.

Uses 5-fold Spatial GroupKFold (grouped by `neighborhood`, 36 LA neighborhoods)
so adjacent 100m tiles never leak across train/test splits.
Compares two feature sets:
  A. Urban Form Only (9 OpenStreetMap land-cover / built-form features)
  B. Urban Form + Macro-Geography (adds dist_to_coast_km, dist_to_dtla_km, elevation_m)

Saves metrics to `data/processed/ml_results_summary.json` and figures to `report/figures/`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import (
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATA_PATH = Path("data/processed/urban_heat_tiles.csv")
SUMMARY_PATH = Path("data/processed/ml_results_summary.json")
FIG_DIR = Path("report/figures")

URBAN_FORM_FEATURES = [
    "osm_building_pct",
    "osm_building_count",
    "osm_road_length_m",
    "osm_major_road_m",
    "osm_green_pct",
    "osm_water_pct",
    "osm_industrial_comm_pct",
    "osm_residential_pct",
    "osm_parking_pct",
]

MACRO_GEO_FEATURES = [
    "dist_to_coast_km",
    "dist_to_dtla_km",
    "elevation_m",
]

FEATURE_SETS = {
    "urban_form_only": URBAN_FORM_FEATURES,
    "urban_form_plus_geo": URBAN_FORM_FEATURES + MACRO_GEO_FEATURES,
}


def build_models() -> dict[str, Any]:
    return {
        "Mean Baseline": DummyRegressor(strategy="mean"),
        "Ridge Regression": make_pipeline(StandardScaler(), Ridge(alpha=10.0)),
        "Random Forest": RandomForestRegressor(
            n_estimators=300, max_depth=12, min_samples_leaf=5, random_state=42, n_jobs=-1
        ),
        "Extra Trees": ExtraTreesRegressor(
            n_estimators=300, max_depth=12, min_samples_leaf=5, random_state=42, n_jobs=-1
        ),
        "HistGradientBoosting": HistGradientBoostingRegressor(
            max_iter=300,
            learning_rate=0.05,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            l2_regularization=1.0,
            random_state=42,
        ),
    }


def evaluate_feature_set(
    df: pd.DataFrame, feature_cols: list[str], target_col: str = "average_temperature"
) -> tuple[list[dict[str, Any]], dict[str, np.ndarray]]:
    X = df[feature_cols]
    y = df[target_col].to_numpy()
    groups = df["neighborhood"].to_numpy()
    cv = GroupKFold(n_splits=5)

    results: list[dict[str, Any]] = []
    oof_preds: dict[str, np.ndarray] = {}

    for name, model in build_models().items():
        preds = cross_val_predict(model, X, y, groups=groups, cv=cv, n_jobs=1)
        oof_preds[name] = preds
        results.append({
            "model": name,
            "mae_c": round(float(mean_absolute_error(y, preds)), 4),
            "rmse_c": round(float(root_mean_squared_error(y, preds)), 4),
            "r2": round(float(r2_score(y, preds)), 4),
        })
    return results, oof_preds


def compute_grouped_permutation_importance(
    df: pd.DataFrame, feature_cols: list[str], model_factory
) -> pd.DataFrame:
    """Compute held-out permutation importance averaged across 5 spatial folds."""
    X = df[feature_cols]
    y = df["average_temperature"].to_numpy()
    groups = df["neighborhood"].to_numpy()
    cv = GroupKFold(n_splits=5)

    fold_imps: list[np.ndarray] = []
    for train_idx, test_idx in cv.split(X, y, groups):
        m = model_factory()
        m.fit(X.iloc[train_idx], y[train_idx])
        perm = permutation_importance(
            m, X.iloc[test_idx], y[test_idx],
            n_repeats=10, random_state=42, scoring="neg_mean_absolute_error", n_jobs=1,
        )
        fold_imps.append(perm.importances_mean)

    mean_imp = np.mean(fold_imps, axis=0)
    std_imp = np.std(fold_imps, axis=0)
    return (
        pd.DataFrame({"feature": feature_cols, "mae_increase_c": mean_imp, "std_c": std_imp})
        .sort_values("mae_increase_c", ascending=False)
        .reset_index(drop=True)
    )


def plot_neighborhood_temps(df: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    nb_stats = (
        df.groupby(["neighborhood_name", "zone"])["average_temperature"]
        .agg(["mean", "min", "max"])
        .reset_index()
        .sort_values("mean")
    )
    fig, ax = plt.subplots(figsize=(10, 9))
    y_pos = np.arange(len(nb_stats))
    ax.hlines(y_pos, nb_stats["min"], nb_stats["max"], color="#9ecae1", linewidth=3, alpha=0.8)
    ax.scatter(nb_stats["mean"], y_pos, color="#08519c", s=45, zorder=3, label="Neighborhood Mean (°C)")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(nb_stats["neighborhood_name"], fontsize=8.5)
    ax.set_xlabel("FortyGuard Modeled Temperature (°C) — 2024-07-15 14:00")
    ax.set_title("LA Basin Heat Gradient Across 36 Neighborhoods (2,507 Tiles)")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "phase4_temp_by_neighborhood.png", dpi=160)
    plt.close(fig)


def plot_model_comparison(summary: dict[str, list[dict[str, Any]]]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df_a = pd.DataFrame(summary["urban_form_only"]).set_index("model")
    df_b = pd.DataFrame(summary["urban_form_plus_geo"]).set_index("model")
    models = df_a.index.tolist()
    x = np.arange(len(models))
    w = 0.36

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].bar(x - w / 2, df_a["mae_c"], width=w, label="Urban Form Only (OSM)", color="#fdae6b")
    axes[0].bar(x + w / 2, df_b["mae_c"], width=w, label="Urban Form + Coast/Elev", color="#2b8cbe")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(models, rotation=20, ha="right", fontsize=9)
    axes[0].set_ylabel("Spatial-CV MAE (°C) — Lower is Better")
    axes[0].set_title("Out-of-Neighborhood MAE (5-Fold GroupKFold)")
    axes[0].grid(axis="y", linestyle="--", alpha=0.4)
    axes[0].legend()

    axes[1].bar(x - w / 2, df_a["r2"], width=w, label="Urban Form Only (OSM)", color="#fdae6b")
    axes[1].bar(x + w / 2, df_b["r2"], width=w, label="Urban Form + Coast/Elev", color="#2b8cbe")
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(models, rotation=20, ha="right", fontsize=9)
    axes[1].set_ylabel("Spatial-CV R² — Higher is Better")
    axes[1].set_title("Out-of-Neighborhood R² (5-Fold GroupKFold)")
    axes[1].grid(axis="y", linestyle="--", alpha=0.4)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(FIG_DIR / "phase4_model_comparison.png", dpi=160)
    plt.close(fig)


def plot_pred_and_importance(
    y_true: np.ndarray, y_pred: np.ndarray, best_name: str, imp_df: pd.DataFrame
) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.0))

    axes[0].scatter(y_true, y_pred, alpha=0.25, s=14, color="#2b8cbe", edgecolors="none")
    lims = [min(y_true.min(), y_pred.min()) - 0.5, max(y_true.max(), y_pred.max()) + 0.5]
    axes[0].plot(lims, lims, "r--", linewidth=1.2, label="Perfect Prediction")
    axes[0].set_xlim(lims)
    axes[0].set_ylim(lims)
    axes[0].set_xlabel("Actual Temperature (°C)")
    axes[0].set_ylabel("Spatial-CV Predicted Temperature (°C)")
    axes[0].set_title(f"{best_name}: Out-of-Neighborhood Predictions")
    axes[0].grid(True, linestyle="--", alpha=0.35)
    axes[0].legend()

    top = imp_df.head(10).iloc[::-1]
    axes[1].barh(top["feature"], top["mae_increase_c"], xerr=top["std_c"], color="#31a354", alpha=0.85)
    axes[1].set_xlabel("Mean MAE Increase When Permuted (°C)")
    axes[1].set_title(f"{best_name}: Spatial-CV Permutation Importance")
    axes[1].grid(axis="x", linestyle="--", alpha=0.35)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "phase4_pred_vs_actual_and_importance.png", dpi=160)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} tiles across {df['neighborhood'].nunique()} neighborhoods.")

    all_results: dict[str, list[dict[str, Any]]] = {}
    all_oof: dict[str, dict[str, np.ndarray]] = {}

    for fs_name, cols in FEATURE_SETS.items():
        res, oof = evaluate_feature_set(df, cols)
        all_results[fs_name] = res
        all_oof[fs_name] = oof
        print(f"\n=== Feature Set: {fs_name} ({len(cols)} features) ===")
        print(pd.DataFrame(res).to_string(index=False))

    # Pick best non-baseline model on urban_form_plus_geo by lowest MAE
    geo_res = [r for r in all_results["urban_form_plus_geo"] if r["model"] != "Mean Baseline"]
    best_model_name = min(geo_res, key=lambda r: r["mae_c"])["model"]
    imp_df = compute_grouped_permutation_importance(
        df,
        FEATURE_SETS["urban_form_plus_geo"],
        lambda: build_models()[best_model_name],
    )
    print(f"\n=== Permutation Importance ({best_model_name}, urban_form_plus_geo) ===")
    print(imp_df.round(4).to_string(index=False))

    plot_neighborhood_temps(df)
    plot_model_comparison(all_results)
    plot_pred_and_importance(
        df["average_temperature"].to_numpy(),
        all_oof["urban_form_plus_geo"][best_model_name],
        best_model_name,
        imp_df,
    )

    summary_payload = {
        "rows": int(len(df)),
        "neighborhoods": int(df["neighborhood"].nunique()),
        "cv_strategy": "5-fold GroupKFold by neighborhood",
        "results": all_results,
        "best_model_geo": best_model_name,
        "permutation_importance_geo": imp_df.round(4).to_dict(orient="records"),
    }
    SUMMARY_PATH.write_text(json.dumps(summary_payload, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved summary to {SUMMARY_PATH} and 3 figures to {FIG_DIR}/")


if __name__ == "__main__":
    main()
