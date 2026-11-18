"""Lazy-loading LSTM prediction service for Nexora's trained artifacts."""

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any

from backend.errors import ApiError
from backend.services.market_data import MarketHistory

FEATURE_NAMES = ("Return", "LogVolume", "MA10_ratio", "MA50_ratio", "Volatility10", "HighLowRange", "RSI")


def calculate_features(history: MarketHistory) -> Any:
    import numpy as np
    closes = np.asarray(history.closes, dtype=np.float64)
    highs = np.asarray(history.highs, dtype=np.float64)
    lows = np.asarray(history.lows, dtype=np.float64)
    volumes = np.asarray(history.volumes, dtype=np.float64)
    rows: list[list[float]] = []

    for index in range(10, len(closes)):
        previous = closes[index - 1]
        daily_return = (closes[index] - previous) / previous if previous else 0.0
        ma10 = closes[index - 9 : index + 1].mean()
        ma50 = closes[max(0, index - 49) : index + 1].mean()
        returns = np.diff(closes[max(0, index - 10) : index + 1]) / closes[max(0, index - 10) : index]
        differences = np.diff(closes[max(0, index - 14) : index + 1])
        average_gain = np.clip(differences, 0, None).mean() if differences.size else 0.0
        average_loss = np.clip(-differences, 0, None).mean() if differences.size else 0.0
        rsi = 100.0 if average_loss == 0 else 100 - (100 / (1 + average_gain / average_loss))
        rows.append([
            daily_return,
            np.log(max(volumes[index], 1)),
            closes[index] / ma10 - 1 if ma10 else 0.0,
            closes[index] / ma50 - 1 if ma50 else 0.0,
            float(np.std(returns)) if returns.size else 0.0,
            (highs[index] - lows[index]) / closes[index] if closes[index] else 0.0,
            rsi,
        ])
    return np.asarray(rows, dtype=np.float64)


class PredictionService:
    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.model_path = self.project_root / "model_weights.pth"
        self.scaler_path = self.project_root / "scaler.pkl"
        self._model = None
        self._scaler = None
        self._lock = Lock()

    @property
    def artifacts_available(self) -> bool:
        return self.model_path.is_file() and self.scaler_path.is_file()

    def _load(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            if not self.artifacts_available:
                raise ApiError("Prediction artifacts are not installed.", 503, "prediction_unavailable")
            try:
                import joblib
                import torch
                import torch.nn as nn

                class LstmModel(nn.Module):
                    def __init__(self):
                        super().__init__()
                        self.lstm = nn.LSTM(len(FEATURE_NAMES), 32, 2, batch_first=True, dropout=0.2)
                        self.drop = nn.Dropout(0.2)
                        self.fc = nn.Linear(32, 1)

                    def forward(self, value):
                        output, _ = self.lstm(value)
                        return self.fc(self.drop(output[:, -1, :]))

                model = LstmModel()
                model.load_state_dict(torch.load(self.model_path, map_location="cpu", weights_only=True))
                model.eval()
                self._model = model
                self._scaler = joblib.load(self.scaler_path)
            except ApiError:
                raise
            except Exception as error:
                raise ApiError("Prediction model could not be loaded.", 503, "prediction_unavailable") from error

    def predict(self, history: MarketHistory) -> dict[str, Any]:
        import numpy as np

        features = calculate_features(history)
        if len(features) < 20:
            raise ApiError("At least 30 trading days are required for a prediction.", 422, "insufficient_history")
        self._load()

        try:
            import torch

            scaled = self._scaler.transform(features[-20:])
            tensor = torch.from_numpy(scaled).float().unsqueeze(0)
            with torch.no_grad():
                scaled_return = float(self._model(tensor).item())
            return_scale = float(self._scaler.scale_[0])
            return_mean = float(self._scaler.mean_[0])
            predicted_return = scaled_return * return_scale + return_mean
        except Exception as error:
            raise ApiError("The prediction could not be calculated.", 500, "prediction_failed") from error

        predicted_price = history.last_price * (1 + predicted_return)
        recent_volatility = float(np.std(features[-20:, 0]))
        confidence = max(0.5, min(0.95, 1 - recent_volatility * 8))
        return {
            "predicted_return": predicted_return,
            "predicted_price": predicted_price,
            "confidence": confidence,
            "model": "lstm-v1",
        }
