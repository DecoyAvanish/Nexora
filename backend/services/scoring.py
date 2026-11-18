"""Explainable stock scoring from technical factors and real-news sentiment."""

from __future__ import annotations

from typing import Any

from backend.errors import ApiError
from backend.services.market_data import MarketHistory


def _clip(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _pct_change(values, periods: int) -> float:
    if len(values) <= periods or values[-periods - 1] == 0:
        return 0.0
    return float(values[-1] / values[-periods - 1] - 1)


class StockScoringService:
    technical_weight = 0.65
    sentiment_weight = 0.35

    def technical_factors(self, history: MarketHistory) -> dict[str, Any]:
        import numpy as np

        closes = np.asarray(history.closes, dtype=float)
        volumes = np.asarray(history.volumes, dtype=float)
        if len(closes) < 126:
            raise ApiError("At least 126 trading days are required for an AI score.", 422, "insufficient_history")

        returns = np.diff(closes) / closes[:-1]
        momentum_21 = _pct_change(closes, 21)
        momentum_63 = _pct_change(closes, 63)
        momentum_126 = _pct_change(closes, 126)
        ma20 = float(closes[-20:].mean())
        ma50 = float(closes[-50:].mean())
        ma200 = float(closes[-min(200, len(closes)):].mean())
        trend = (closes[-1] / ma20 - 1) * 8 + (closes[-1] / ma50 - 1) * 5 + (closes[-1] / ma200 - 1) * 3

        differences = np.diff(closes[-15:])
        gains = np.clip(differences, 0, None).mean()
        losses = np.clip(-differences, 0, None).mean()
        rsi = 100.0 if losses == 0 else float(100 - 100 / (1 + gains / losses))
        rsi_signal = _clip((rsi - 50) / 30)
        if rsi > 75:
            rsi_signal -= min((rsi - 75) / 15, 0.5)

        ema12 = self._ema(closes, 12)
        ema26 = self._ema(closes, 26)
        macd_ratio = (ema12 - ema26) / closes[-1]
        volatility_21 = float(np.std(returns[-21:]) * np.sqrt(252))
        volatility_signal = _clip((0.35 - volatility_21) / 0.25)
        rolling_high = float(np.max(closes[-min(252, len(closes)):]))
        drawdown = float(closes[-1] / rolling_high - 1)
        volume_ratio = float(volumes[-20:].mean() / max(volumes[-60:].mean(), 1))
        volume_direction = 1 if momentum_21 >= 0 else -1

        signals = {
            "momentum_1m": _clip(momentum_21 * 5),
            "momentum_3m": _clip(momentum_63 * 3),
            "momentum_6m": _clip(momentum_126 * 2),
            "trend_strength": _clip(float(trend)),
            "rsi": _clip(rsi_signal),
            "macd": _clip(float(macd_ratio * 35)),
            "volatility": volatility_signal,
            "drawdown": _clip(1 + drawdown * 4),
            "volume_confirmation": _clip((volume_ratio - 1) * 3 * volume_direction),
        }
        weights = {
            "momentum_1m": 0.12,
            "momentum_3m": 0.17,
            "momentum_6m": 0.13,
            "trend_strength": 0.18,
            "rsi": 0.08,
            "macd": 0.10,
            "volatility": 0.10,
            "drawdown": 0.07,
            "volume_confirmation": 0.05,
        }
        technical_score = sum(signals[name] * weights[name] for name in signals)
        metrics = {
            "return_21d": momentum_21,
            "return_63d": momentum_63,
            "return_126d": momentum_126,
            "rsi_14": rsi,
            "annualized_volatility_21d": volatility_21,
            "distance_from_52w_high": drawdown,
            "volume_ratio_20d_to_60d": volume_ratio,
        }
        return {"score": _clip(float(technical_score)), "signals": signals, "metrics": metrics}

    def score(self, history: MarketHistory, sentiment: dict[str, Any]) -> dict[str, Any]:
        technical = self.technical_factors(history)
        sentiment_score = _clip(float(sentiment.get("sentiment_score", 0.0)))
        article_count = int(sentiment.get("article_count", 0))
        news_coverage = min(article_count / 10, 1.0)
        effective_sentiment_weight = self.sentiment_weight * news_coverage
        effective_technical_weight = 1 - effective_sentiment_weight
        composite = technical["score"] * effective_technical_weight + sentiment_score * effective_sentiment_weight
        ai_score = max(1, min(10, int(round(5.5 + composite * 4.5))))
        signal = self._signal(ai_score)

        drivers = [
            {
                "name": name,
                "category": "technical",
                "direction": "positive" if value >= 0 else "negative",
                "impact": abs(value),
            }
            for name, value in technical["signals"].items()
        ]
        if article_count:
            drivers.append({
                "name": "financial_news_sentiment",
                "category": "sentiment",
                "direction": "positive" if sentiment_score >= 0 else "negative",
                "impact": abs(sentiment_score),
            })
        drivers.sort(key=lambda item: item["impact"], reverse=True)

        return {
            "ai_score": ai_score,
            "signal": signal,
            "components": {
                "technical": round((technical["score"] + 1) * 50, 2),
                "sentiment": round((sentiment_score + 1) * 50, 2),
                "news_coverage": round(news_coverage * 100, 2),
            },
            "technical_metrics": technical["metrics"],
            "top_drivers": drivers[:6],
            "methodology": {
                "technical_weight": round(effective_technical_weight, 3),
                "sentiment_weight": round(effective_sentiment_weight, 3),
                "relative_decile": False,
                "note": "A live composite score; train the cross-sectional model for universe-relative deciles.",
            },
        }

    @staticmethod
    def _ema(values, span: int) -> float:
        alpha = 2 / (span + 1)
        result = float(values[0])
        for value in values[1:]:
            result = alpha * float(value) + (1 - alpha) * result
        return result

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
