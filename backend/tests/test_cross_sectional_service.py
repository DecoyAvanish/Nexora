import json

import joblib
import pandas as pd

from backend.services.cross_sectional import CrossSectionalScoreService


class FakeBundle:
    feature_columns = ["momentum_universe_rank"]

    def contributions(self, frame):
        return [[0.4, 0.0]]


def test_production_score_exposes_probability_percentiles_and_version(tmp_path):
    root = tmp_path / "cross_sectional"
    version = root / "2026.11.18"
    version.mkdir(parents=True)
    manifest = {
        "model_version": "2026.11.18",
        "data_through": "2026-11-17",
        "universe": "S&P 500",
        "horizon_trading_days": 63,
        "mean_model_auc": 0.61,
        "mean_momentum_auc": 0.54,
        "mean_information_coefficient": 0.04,
    }
    (root / "latest.json").write_text(json.dumps(manifest))
    pd.DataFrame([{
        "ticker": "AAPL",
        "sector": "Information Technology",
        "probability": 0.67,
        "ai_score": 9,
        "universe_percentile": 93,
        "sector_percentile": 88,
        "momentum_universe_rank": 0.91,
    }]).to_csv(version / "daily_scores.csv", index=False)
    joblib.dump(FakeBundle(), version / "model.joblib")

    result = CrossSectionalScoreService(root).get_score("aapl")
    assert result["ai_score"] == 9
    assert result["outperformance_probability"] == 0.67
    assert result["universe_percentile"] == 93
    assert result["sector_percentile"] == 88
    assert result["model_version"] == "2026.11.18"
    assert result["data_through"] == "2026-11-17"
