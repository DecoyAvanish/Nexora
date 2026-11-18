"""Purged walk-forward training for Nexora's cross-sectional stock model."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

IDENTIFIER_COLUMNS = {"date", "ticker", "fwd_ret_63d", "bench_ret_63d", "y"}


@dataclass
class FoldMetrics:
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    rows: int
    auc: float
    information_coefficient: float
    decile_spread: float


def prepare_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    required = {"date", "ticker", "fwd_ret_63d", "bench_ret_63d"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"], utc=True)
    data["y"] = (data["fwd_ret_63d"] > data["bench_ret_63d"]).astype(int)
    feature_columns = [column for column in data.columns if column not in IDENTIFIER_COLUMNS]
    if not feature_columns:
        raise ValueError("No feature columns were found.")
    data[feature_columns] = data.groupby("date")[feature_columns].rank(pct=True)
    data = data.dropna(subset=feature_columns + ["fwd_ret_63d", "bench_ret_63d"])
    return data.sort_values(["date", "ticker"]), feature_columns


def assign_deciles(probabilities: pd.Series) -> pd.Series:
    count = len(probabilities)
    if count < 10:
        return pd.Series(np.ceil(probabilities.rank(method="first", pct=True) * 10), index=probabilities.index).clip(1, 10).astype(int)
    return pd.qcut(probabilities.rank(method="first"), 10, labels=False).astype(int) + 1


def train_walk_forward(
    data: pd.DataFrame,
    feature_columns: list[str],
    *,
    train_days: int = 756,
    test_days: int = 63,
    embargo_days: int = 63,
):
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score

    dates = np.array(sorted(data["date"].unique()))
    folds: list[FoldMetrics] = []
    scored_frames = []
    final_model = None
    minimum = train_days + embargo_days
    for test_start in range(minimum, len(dates), test_days):
        test_end = min(test_start + test_days, len(dates))
        train_start = max(0, test_start - embargo_days - train_days)
        train_end = test_start - embargo_days
        train_dates = dates[train_start:train_end]
        test_dates = dates[test_start:test_end]
        if not len(train_dates) or not len(test_dates):
            continue
        train = data[data["date"].isin(train_dates)]
        test = data[data["date"].isin(test_dates)].copy()
        model = lgb.LGBMClassifier(
            objective="binary",
            n_estimators=500,
            learning_rate=0.02,
            num_leaves=31,
            subsample=0.8,
            subsample_freq=1,
            colsample_bytree=0.3,
            min_child_samples=250,
            reg_alpha=0.2,
            reg_lambda=0.5,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(train[feature_columns], train["y"])
        test["probability"] = model.predict_proba(test[feature_columns])[:, 1]
        test["ai_score"] = test.groupby("date")["probability"].transform(assign_deciles)
        excess_return = test["fwd_ret_63d"] - test["bench_ret_63d"]
        ic = test["probability"].corr(excess_return, method="spearman")
        spread = test.loc[test["ai_score"] == 10, "fwd_ret_63d"].mean() - test.loc[test["ai_score"] == 1, "fwd_ret_63d"].mean()
        folds.append(FoldMetrics(
            str(train_dates[0]), str(train_dates[-1]), str(test_dates[0]), str(test_dates[-1]),
            len(test), float(roc_auc_score(test["y"], test["probability"])), float(ic), float(spread),
        ))
        scored_frames.append(test[["date", "ticker", "probability", "ai_score", "fwd_ret_63d", "bench_ret_63d"]])
        final_model = model
    if final_model is None:
        raise ValueError("Not enough dated observations for one purged walk-forward fold.")
    return final_model, folds, pd.concat(scored_frames, ignore_index=True)


def main() -> None:
    import joblib

    parser = argparse.ArgumentParser(description="Train Nexora's cross-sectional LightGBM model.")
    parser.add_argument("dataset", type=Path, help="Point-in-time CSV or Parquet feature dataset")
    parser.add_argument("--output", type=Path, default=Path("artifacts/cross_sectional_model.joblib"))
    parser.add_argument("--train-days", type=int, default=756)
    parser.add_argument("--test-days", type=int, default=63)
    parser.add_argument("--embargo-days", type=int, default=63)
    args = parser.parse_args()
    frame = pd.read_parquet(args.dataset) if args.dataset.suffix == ".parquet" else pd.read_csv(args.dataset)
    data, features = prepare_frame(frame)
    model, folds, scores = train_walk_forward(data, features, train_days=args.train_days, test_days=args.test_days, embargo_days=args.embargo_days)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": features, "trained_through": str(data["date"].max())}, args.output)
    scores.to_csv(args.output.with_suffix(".walk_forward.csv"), index=False)
    args.output.with_suffix(".metrics.json").write_text(json.dumps([asdict(fold) for fold in folds], indent=2))


if __name__ == "__main__":
    main()
