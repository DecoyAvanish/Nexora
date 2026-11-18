"""Serve the latest versioned cross-sectional model scores."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

import pandas as pd

from backend.errors import ApiError
from backend.services.market_data import normalize_symbol


class CrossSectionalScoreService:
    def __init__(self, artifact_root: Path | str = "artifacts/cross_sectional"):
        self.artifact_root = Path(artifact_root)
        self._manifest: dict[str, Any] | None = None
        self._scores: pd.DataFrame | None = None
        self._bundle = None
        self._manifest_mtime: float | None = None
        self._lock = Lock()

    @property
    def available(self) -> bool:
        return (self.artifact_root / "latest.json").is_file()

    def _load(self) -> None:
        import joblib

        manifest_path = self.artifact_root / "latest.json"
        if not manifest_path.is_file():
            raise ApiError("No production cross-sectional model has been published yet.", 503, "model_not_published")
        modified = manifest_path.stat().st_mtime
        if self._scores is not None and self._manifest_mtime == modified:
            return
        with self._lock:
            if self._scores is not None and self._manifest_mtime == modified:
                return
            manifest = json.loads(manifest_path.read_text())
            version = manifest["model_version"]
            version_directory = self.artifact_root / version
            scores_path = version_directory / "daily_scores.csv"
            model_path = version_directory / "model.joblib"
            if not scores_path.is_file() or not model_path.is_file():
                raise ApiError("The published model artifact is incomplete.", 503, "model_artifact_incomplete")
            scores = pd.read_csv(scores_path)
            scores["ticker"] = scores["ticker"].astype(str).str.upper()
            self._manifest = manifest
            self._scores = scores.set_index("ticker", drop=False)
            self._bundle = joblib.load(model_path)
            self._manifest_mtime = modified

    def get_score(self, raw_symbol: str) -> dict[str, Any]:
        symbol = normalize_symbol(raw_symbol)
        self._load()
        if symbol not in self._scores.index:
            raise ApiError(f"{symbol} is not in the current production universe.", 404, "symbol_not_in_universe")
        row = self._scores.loc[symbol]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[-1]
        ai_score = int(row["ai_score"])
        return {
            "ai_score": ai_score,
            "outperformance_probability": float(row["probability"]),
            "universe_percentile": float(row["universe_percentile"]),
            "sector_percentile": float(row.get("sector_percentile", row["universe_percentile"])),
            "sector": row.get("sector"),
            "model_version": self._manifest["model_version"],
            "data_through": self._manifest["data_through"],
            "model_type": "calibrated_cross_sectional_lightgbm",
            "universe": self._manifest["universe"],
            "horizon_trading_days": self._manifest["horizon_trading_days"],
            "signal": self._signal(ai_score),
            "top_drivers": self._top_drivers(row),
            "model_metrics": {
                "walk_forward_auc": self._manifest.get("mean_model_auc"),
                "momentum_baseline_auc": self._manifest.get("mean_momentum_auc"),
                "information_coefficient": self._manifest.get("mean_information_coefficient"),
            },
            "methodology": {"relative_decile": True, "probability_calibrated": True, "embargo_trading_days": 63},
        }

    def explain(self, raw_symbol: str) -> dict[str, Any]:
        symbol=normalize_symbol(raw_symbol); self._load()
        if symbol not in self._scores.index: raise ApiError(f"{symbol} is not in the current production universe.",404,"symbol_not_in_universe")
        row=self._scores.loc[symbol]; row=row.iloc[-1] if isinstance(row,pd.DataFrame) else row
        try:
            values=self._bundle.contributions(pd.DataFrame([row]))[0]; baseline=float(values[-1]); items=[]
            for name,value in zip(self._bundle.feature_columns,values[:-1]):
                category="sentiment" if "sentiment" in name else "fundamental" if any(term in name for term in ("revenue","margin","roe","roic","debt","earnings","valuation","cash_flow")) else "technical"
                feature_value=row.get(name)
                items.append({"feature":name,"label":name.replace("_"," ").title(),"value":float(value),"feature_value":float(feature_value) if pd.notna(feature_value) else None,"direction":"positive" if value>=0 else "negative","category":category,"scope":"sector_relative" if name.endswith("_sector_rank") else "universe_relative"})
            items.sort(key=lambda item:abs(item["value"]),reverse=True)
            return {"baseline":baseline,"waterfall":items,"top_positive":[item for item in items if item["value"]>0][:6],"top_negative":[item for item in items if item["value"]<0][:6]}
        except Exception:
            return {"baseline":None,"waterfall":[],"top_positive":[],"top_negative":[]}

    def _top_drivers(self, row: pd.Series) -> list[dict[str, Any]]:
        try:
            frame = pd.DataFrame([row])
            contributions = self._bundle.contributions(frame)[0][:-1]
            drivers = []
            for name, value in zip(self._bundle.feature_columns, contributions):
                drivers.append({
                    "name": name,
                    "category": "sector_relative" if name.endswith("_sector_rank") else "universe_relative",
                    "direction": "positive" if value >= 0 else "negative",
                    "impact": abs(float(value)),
                    "contribution": float(value),
                })
            return sorted(drivers, key=lambda item: item["impact"], reverse=True)[:6]
        except Exception:
            return []

    @staticmethod
    def _signal(ai_score: int) -> dict[str, str]:
        if ai_score >= 9:
            return {"key": "strong_buy", "label": "STRONG BUY", "color": "green", "hex": "#22c55e"}
        if ai_score >= 7:
            return {"key": "buy", "label": "BUY", "color": "green", "hex": "#4bff9b"}
        if ai_score >= 5:
            return {"key": "hold", "label": "HOLD", "color": "amber", "hex": "#f59e0b"}
        if ai_score >= 3:
            return {"key": "risk", "label": "RISK", "color": "red", "hex": "#fb7185"}
        return {"key": "strong_risk", "label": "STRONG RISK", "color": "red", "hex": "#ef4444"}
