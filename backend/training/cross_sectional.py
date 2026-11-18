"""Calibrated, purged walk-forward training for Nexora's stock-ranking model."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

NON_FEATURE_COLUMNS = {"date", "ticker", "company", "sector", "sub_industry", "membership_as_of", "fwd_ret_63d", "bench_ret_63d", "y"}


@dataclass
class FoldMetrics:
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    rows: int
    model_auc: float
    model_information_coefficient: float
    model_decile_spread: float
    momentum_auc: float
    momentum_information_coefficient: float
    neutral_auc: float = 0.5


@dataclass
class CalibratedModel:
    model: object
    calibrator: object
    feature_columns: list[str]

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        raw = self.model.predict_proba(frame[self.feature_columns])[:, 1]
        calibrated = self.calibrator.predict_proba(raw.reshape(-1, 1))[:, 1]
        return np.column_stack([1 - calibrated, calibrated])

    def contributions(self, frame: pd.DataFrame) -> np.ndarray:
        return self.model.predict(frame[self.feature_columns], pred_contrib=True)


def prepare_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    required = {"date", "ticker", "fwd_ret_63d", "bench_ret_63d"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"], utc=True)
    has_label = data["fwd_ret_63d"].notna() & data["bench_ret_63d"].notna()
    data["y"] = np.where(has_label, (data["fwd_ret_63d"] > data["bench_ret_63d"]).astype(int), np.nan)
    ranked_columns = [column for column in data.columns if column.endswith("_universe_rank") or column.endswith("_sector_rank")]
    if ranked_columns:
        feature_columns = ranked_columns
    else:
        raw_features = [column for column in data.select_dtypes(include=[np.number]).columns if column not in NON_FEATURE_COLUMNS]
        feature_columns = []
        for column in raw_features:
            universe_rank = f"{column}_universe_rank"
            data[universe_rank] = data.groupby("date")[column].rank(pct=True)
            feature_columns.append(universe_rank)
            if "sector" in data:
                sector_rank = f"{column}_sector_rank"
                data[sector_rank] = data.groupby(["date", "sector"])[column].rank(pct=True)
                feature_columns.append(sector_rank)
    if not feature_columns:
        raise ValueError("No numeric feature columns were found.")
    return data.dropna(subset=feature_columns).sort_values(["date", "ticker"]), feature_columns


def assign_deciles(probabilities: pd.Series) -> pd.Series:
    if len(probabilities) < 10:
        return np.ceil(probabilities.rank(method="first", pct=True) * 10).clip(1, 10).astype(int)
    return pd.qcut(probabilities.rank(method="first"), 10, labels=False).astype(int) + 1


def _new_model():
    import lightgbm as lgb
    return lgb.LGBMClassifier(objective="binary", n_estimators=500, learning_rate=0.02, num_leaves=31, subsample=0.8, subsample_freq=1, colsample_bytree=0.3, min_child_samples=250, reg_alpha=0.2, reg_lambda=0.5, random_state=42, n_jobs=-1, verbosity=-1, importance_type="gain")


def fit_calibrated_model(train: pd.DataFrame, feature_columns: list[str], calibration_days: int = 63) -> CalibratedModel:
    from sklearn.linear_model import LogisticRegression

    dates = np.array(sorted(train["date"].unique()))
    if len(dates) <= calibration_days:
        raise ValueError("Training data does not contain enough dates for probability calibration.")
    calibration_dates = dates[-calibration_days:]
    fit = train[~train["date"].isin(calibration_dates)]
    calibration = train[train["date"].isin(calibration_dates)]
    model = _new_model()
    model.fit(fit[feature_columns], fit["y"].astype(int))
    raw_probability = model.predict_proba(calibration[feature_columns])[:, 1]
    calibrator = LogisticRegression(random_state=42)
    calibrator.fit(raw_probability.reshape(-1, 1), calibration["y"].astype(int))
    return CalibratedModel(model, calibrator, feature_columns)


def _safe_auc(labels, probability) -> float:
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(labels, probability)) if pd.Series(labels).nunique() > 1 else 0.5


def train_walk_forward(data: pd.DataFrame, feature_columns: list[str], *, train_days: int = 756, test_days: int = 63, embargo_days: int = 63, calibration_days: int = 63):
    labeled = data.dropna(subset=["y"]).copy()
    dates = np.array(sorted(labeled["date"].unique()))
    folds: list[FoldMetrics] = []
    scored_frames = []
    importance_frames = []
    momentum_column = "return_126d_universe_rank"
    for test_start in range(train_days + embargo_days, len(dates), test_days):
        test_end = min(test_start + test_days, len(dates))
        train_start = max(0, test_start - embargo_days - train_days)
        train_dates = dates[train_start : test_start - embargo_days]
        test_dates = dates[test_start:test_end]
        if len(train_dates) <= calibration_days or not len(test_dates):
            continue
        train = labeled[labeled["date"].isin(train_dates)]
        test = labeled[labeled["date"].isin(test_dates)].copy()
        bundle = fit_calibrated_model(train, feature_columns, calibration_days)
        test["probability"] = bundle.predict_proba(test)[:, 1]
        test["ai_score"] = test.groupby("date")["probability"].transform(assign_deciles)
        test["universe_percentile"] = test.groupby("date")["probability"].rank(pct=True) * 100
        if "sector" in test:
            test["sector_percentile"] = test.groupby(["date", "sector"])["probability"].rank(pct=True) * 100
        excess_return = test["fwd_ret_63d"] - test["bench_ret_63d"]
        momentum = test[momentum_column] if momentum_column in test else test[feature_columns[0]]
        technical_columns = [column for column in feature_columns if any(token in column for token in ("return_", "ma20_", "ma50_", "ma200_", "rsi_", "drawdown_", "volume_"))]
        test["momentum_probability"] = momentum
        test["technical_probability"] = test[technical_columns].mean(axis=1) if technical_columns else momentum
        sentiment_column = next((column for column in feature_columns if "sentiment" in column and column.endswith("_universe_rank")), None)
        test["sentiment_probability"] = test[sentiment_column] if sentiment_column else np.nan
        test["random_probability"] = [int(hashlib.sha256(f"{date}|{ticker}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF for date, ticker in zip(test["date"], test["ticker"])]
        spread = test.loc[test["ai_score"] == 10, "fwd_ret_63d"].mean() - test.loc[test["ai_score"] == 1, "fwd_ret_63d"].mean()
        folds.append(FoldMetrics(str(train_dates[0]), str(train_dates[-1]), str(test_dates[0]), str(test_dates[-1]), len(test), _safe_auc(test["y"], test["probability"]), float(test["probability"].corr(excess_return, method="spearman")), float(spread), _safe_auc(test["y"], momentum), float(momentum.corr(excess_return, method="spearman"))))
        columns = ["date", "ticker", "sector", "probability", "momentum_probability", "technical_probability", "sentiment_probability", "random_probability", "ai_score", "universe_percentile", "sector_percentile", "fwd_ret_63d", "bench_ret_63d", "y"]
        scored_frames.append(test[[column for column in columns if column in test]])
        importance_frames.append(pd.DataFrame({"fold": len(folds), "feature": feature_columns, "importance": bundle.model.feature_importances_}))
    if not folds:
        raise ValueError("Not enough observations for one calibrated purged walk-forward fold.")
    return fit_calibrated_model(labeled, feature_columns, calibration_days), folds, pd.concat(scored_frames, ignore_index=True), pd.concat(importance_frames, ignore_index=True)


def score_latest_snapshot(bundle: CalibratedModel, data: pd.DataFrame) -> pd.DataFrame:
    latest = data[data["date"] == data["date"].max()].copy()
    latest["probability"] = bundle.predict_proba(latest)[:, 1]
    latest["ai_score"] = assign_deciles(latest["probability"])
    latest["universe_percentile"] = latest["probability"].rank(pct=True) * 100
    if "sector" in latest:
        latest["sector_percentile"] = latest.groupby("sector")["probability"].rank(pct=True) * 100
    return latest


def publish_artifact(bundle: CalibratedModel, folds: list[FoldMetrics], walk_forward_scores: pd.DataFrame, latest_scores: pd.DataFrame, feature_importance: pd.DataFrame, artifact_root: Path) -> Path:
    import joblib

    data_through = pd.Timestamp(latest_scores["date"].max()).date().isoformat()
    version = pd.Timestamp(data_through).strftime("%Y.%m.%d")
    version_directory = artifact_root / version
    version_directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, version_directory / "model.joblib")
    walk_forward_scores.to_csv(version_directory / "walk_forward_scores.csv", index=False)
    latest_scores.to_csv(version_directory / "daily_scores.csv", index=False)
    feature_importance.to_csv(version_directory / "feature_importance_by_fold.csv", index=False)
    metrics = [asdict(fold) for fold in folds]
    (version_directory / "metrics.json").write_text(json.dumps(metrics, indent=2))
    manifest = {"model_version": version, "data_through": data_through, "created_at": datetime.now(timezone.utc).isoformat(), "universe": "S&P 500", "horizon_trading_days": 63, "feature_count": len(bundle.feature_columns), "fold_count": len(folds), "artifact_directory": str(version_directory), "mean_model_auc": float(np.mean([fold.model_auc for fold in folds])), "mean_momentum_auc": float(np.mean([fold.momentum_auc for fold in folds])), "mean_information_coefficient": float(np.mean([fold.model_information_coefficient for fold in folds]))}
    (version_directory / "manifest.json").write_text(json.dumps(manifest, indent=2))
    artifact_root.mkdir(parents=True, exist_ok=True)
    (artifact_root / "latest.json").write_text(json.dumps(manifest, indent=2))
    from backend.evaluation.model_lab import write_model_lab_report
    write_model_lab_report(version_directory)
    return version_directory


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and publish Nexora's calibrated cross-sectional model.")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/cross_sectional"))
    parser.add_argument("--train-days", type=int, default=756)
    parser.add_argument("--test-days", type=int, default=63)
    parser.add_argument("--embargo-days", type=int, default=63)
    parser.add_argument("--calibration-days", type=int, default=63)
    args = parser.parse_args()
    frame = pd.read_parquet(args.dataset) if args.dataset.suffix == ".parquet" else pd.read_csv(args.dataset)
    data, features = prepare_frame(frame)
    bundle, folds, scores, importance = train_walk_forward(data, features, train_days=args.train_days, test_days=args.test_days, embargo_days=args.embargo_days, calibration_days=args.calibration_days)
    output = publish_artifact(bundle, folds, scores, score_latest_snapshot(bundle, data), importance, args.artifacts)
    print(f"Published calibrated model to {output}")


if __name__ == "__main__":
    main()
