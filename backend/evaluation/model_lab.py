"""Generate an honest public evaluation report from walk-forward predictions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

STRATEGIES = {
    "cross_sectional_model": "probability",
    "simple_momentum": "momentum_probability",
    "random_selection": "random_probability",
    "technical_only": "technical_probability",
    "sentiment_only": "sentiment_probability",
}


def _max_drawdown(returns: pd.Series) -> float:
    wealth = (1 + returns.fillna(0)).cumprod()
    return float((wealth / wealth.cummax() - 1).min()) if len(wealth) else 0.0


def _performance_metrics(returns: pd.Series, turnover: pd.Series, cost_bps: float) -> dict[str, Any]:
    returns = returns.dropna()
    if returns.empty:
        return {"available": False, "reason": "No point-in-time predictions were available."}
    net = returns - turnover.reindex(returns.index).fillna(0) * cost_bps / 10_000
    downside = net[net < 0]
    volatility = net.std(ddof=1)
    downside_deviation = downside.std(ddof=1) if len(downside) > 1 else np.nan
    return {
        "available": True,
        "periods": len(net),
        "gross_cumulative_return": float((1 + returns).prod() - 1),
        "transaction_cost_adjusted_return": float((1 + net).prod() - 1),
        "maximum_drawdown": _max_drawdown(net),
        "sharpe_ratio": float(net.mean() / volatility * np.sqrt(4)) if volatility and not np.isnan(volatility) else None,
        "sortino_ratio": float(net.mean() / downside_deviation * np.sqrt(4)) if downside_deviation and not np.isnan(downside_deviation) else None,
        "average_turnover": float(turnover.mean()),
        "transaction_cost_bps": cost_bps,
        "period_returns": [{"date": str(index.date()), "gross": float(returns.loc[index]), "net": float(net.loc[index])} for index in net.index],
    }


def _strategy_returns(scores: pd.DataFrame, probability_column: str) -> tuple[pd.Series, pd.Series]:
    dates = sorted(scores["date"].unique())[::63]
    returns = {}
    turnover = {}
    previous_long: set[str] = set()
    previous_short: set[str] = set()
    for current_date in dates:
        snapshot = scores[scores["date"] == current_date].dropna(subset=[probability_column])
        if len(snapshot) < 20:
            continue
        ranked = snapshot.sort_values(probability_column)
        count = max(1, len(ranked) // 10)
        short = ranked.head(count)
        long = ranked.tail(count)
        returns[pd.Timestamp(current_date)] = float(long["fwd_ret_63d"].mean() - short["fwd_ret_63d"].mean())
        long_set, short_set = set(long["ticker"]), set(short["ticker"])
        if previous_long:
            long_turnover = 1 - len(long_set & previous_long) / max(len(long_set), 1)
            short_turnover = 1 - len(short_set & previous_short) / max(len(short_set), 1)
            turnover[pd.Timestamp(current_date)] = (long_turnover + short_turnover) / 2
        else:
            turnover[pd.Timestamp(current_date)] = 1.0
        previous_long, previous_short = long_set, short_set
    return pd.Series(returns, dtype=float), pd.Series(turnover, dtype=float)


def _calibration_curve(scores: pd.DataFrame) -> list[dict[str, Any]]:
    valid = scores.dropna(subset=["probability", "y"]).copy()
    valid["bin"] = pd.cut(valid["probability"], bins=np.linspace(0, 1, 11), include_lowest=True)
    curve = valid.groupby("bin", observed=True).agg(predicted_probability=("probability", "mean"), observed_frequency=("y", "mean"), count=("y", "size"))
    return [{"predicted_probability": float(row.predicted_probability), "observed_frequency": float(row.observed_frequency), "count": int(row.count)} for row in curve.itertuples()]


def _feature_stability(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"available": False, "reason": "Feature importance will be available after the next retraining run."}
    importance = pd.read_csv(path)
    pivot = importance.pivot(index="fold", columns="feature", values="importance").fillna(0)
    correlations = [pivot.loc[left].corr(pivot.loc[right], method="spearman") for left, right in zip(pivot.index[:-1], pivot.index[1:])]
    summary = importance.groupby("feature")["importance"].agg(["mean", "std"]).fillna(0).sort_values("mean", ascending=False).head(15)
    return {
        "available": True,
        "mean_consecutive_fold_rank_correlation": float(np.nanmean(correlations)),
        "top_features": [{"feature": feature, "mean_importance": float(row["mean"]), "standard_deviation": float(row["std"])} for feature, row in summary.iterrows()],
    }


def build_model_lab_report(version_directory: Path, cost_bps: float = 10) -> dict[str, Any]:
    manifest = json.loads((version_directory / "manifest.json").read_text())
    scores = pd.read_csv(version_directory / "walk_forward_scores.csv", parse_dates=["date"])
    if "y" not in scores:
        scores["y"] = (scores["fwd_ret_63d"] > scores["bench_ret_63d"]).astype(int)
    folds = json.loads((version_directory / "metrics.json").read_text())
    strategy_metrics = {}
    strategy_period_returns = {}
    for name, column in STRATEGIES.items():
        if column not in scores or scores[column].notna().sum() == 0:
            strategy_metrics[name] = {"available": False, "reason": "Required point-in-time feature history is not available in this model version."}
            continue
        returns, turnover = _strategy_returns(scores, column)
        strategy_metrics[name] = _performance_metrics(returns, turnover, cost_bps)
        strategy_period_returns[name] = returns

    evaluation_dates = sorted(scores["date"].unique())[::63]
    spy_returns = scores[scores["date"].isin(evaluation_dates)].groupby("date")["bench_ret_63d"].mean()
    strategy_metrics["buy_and_hold_spy"] = _performance_metrics(spy_returns, pd.Series(0.0, index=spy_returns.index), 0)

    baseline_comparison = {}
    for name, column in STRATEGIES.items():
        if column not in scores or scores[column].notna().sum() == 0:
            baseline_comparison[name] = {"available": False, "auc": None}
            continue
        valid = scores.dropna(subset=[column, "y"])
        baseline_comparison[name] = {"available": True, "auc": float(roc_auc_score(valid["y"], valid[column]))}
    baseline_comparison["buy_and_hold_spy"] = {"available": True, "auc": None, "note": "Return benchmark; AUC is not applicable."}

    model_returns = strategy_period_returns.get("cross_sectional_model", pd.Series(dtype=float))
    regimes = {}
    if not model_returns.empty:
        benchmark = scores.groupby("date")["bench_ret_63d"].mean().reindex(model_returns.index)
        labels = pd.cut(benchmark, [-np.inf, -0.05, 0.05, np.inf], labels=["bear", "sideways", "bull"])
        for regime in ("bull", "bear", "sideways"):
            subset = model_returns[labels == regime]
            regimes[regime] = {"periods": len(subset), "average_long_short_return": float(subset.mean()) if len(subset) else None, "cumulative_long_short_return": float((1 + subset).prod() - 1) if len(subset) else None}

    return {
        "model_version": manifest["model_version"],
        "data_through": manifest["data_through"],
        "universe": manifest["universe"],
        "horizon_trading_days": manifest["horizon_trading_days"],
        "walk_forward": {
            "folds": len(folds),
            "mean_auc": float(np.mean([fold["model_auc"] for fold in folds])),
            "mean_information_coefficient": float(np.mean([fold["model_information_coefficient"] for fold in folds])),
            "mean_top_bottom_decile_spread": float(np.mean([fold["model_decile_spread"] for fold in folds])),
            "fold_metrics": folds,
        },
        "performance": strategy_metrics,
        "baseline_comparison": baseline_comparison,
        "market_regimes": regimes,
        "calibration_curve": _calibration_curve(scores),
        "feature_importance_stability": _feature_stability(version_directory / "feature_importance_by_fold.csv"),
        "methodology": {
            "rebalance_frequency_trading_days": 63,
            "transaction_cost_bps": cost_bps,
            "purged_embargo_trading_days": 63,
            "probability_calibration": "Platt scaling on the final 63 training dates",
            "limitations": [
                "The current constituent snapshot creates historical survivorship bias until point-in-time membership history is added.",
                "Sentiment-only comparison is unavailable until historical point-in-time news features cover the full evaluation period.",
                "Paper results do not guarantee future performance.",
            ],
        },
    }


def write_model_lab_report(version_directory: Path) -> Path:
    output = version_directory / "model_lab.json"
    output.write_text(json.dumps(build_model_lab_report(version_directory), indent=2, allow_nan=False))
    return output
