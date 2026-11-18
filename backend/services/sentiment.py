"""Finance-specific headline sentiment using ProsusAI FinBERT."""

from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Any, Callable

from backend.errors import ApiError
from backend.services.news import NewsArticle

FINBERT_MODEL = "ProsusAI/finbert"


class SentimentService:
    def __init__(self, classifier: Callable | None = None, model_name: str = FINBERT_MODEL):
        self.model_name = model_name
        self._classifier = classifier
        self._lock = Lock()

    def _load_classifier(self):
        if self._classifier is not None:
            return self._classifier
        with self._lock:
            if self._classifier is not None:
                return self._classifier
            try:
                from transformers import pipeline

                self._classifier = pipeline(
                    "text-classification",
                    model=self.model_name,
                    tokenizer=self.model_name,
                    device=-1,
                )
            except Exception as error:
                raise ApiError(
                    "The financial sentiment model is not available. Install its dependencies and allow the first model download.",
                    503,
                    "sentiment_model_unavailable",
                ) from error
        return self._classifier

    def analyze(self, articles: list[NewsArticle]) -> dict[str, Any]:
        if not articles:
            return {
                "model": self.model_name,
                "article_count": 0,
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "label": "neutral",
                "distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "articles": [],
            }

        classifier = self._load_classifier()
        headlines = [article.title[:512] for article in articles]
        try:
            predictions = classifier(headlines, truncation=True, batch_size=16)
        except Exception as error:
            raise ApiError("Headline sentiment analysis failed.", 503, "sentiment_failed") from error

        analyzed = []
        weighted_scores = []
        confidences = []
        labels = []
        polarity = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        for article, prediction in zip(articles, predictions):
            label = str(prediction.get("label", "neutral")).lower()
            if label not in polarity:
                label = "neutral"
            confidence = max(0.0, min(float(prediction.get("score", 0.0)), 1.0))
            weighted_scores.append(polarity[label] * confidence)
            confidences.append(confidence)
            labels.append(label)
            analyzed.append({**article.to_dict(), "sentiment": label, "sentiment_confidence": confidence})

        average = sum(weighted_scores) / len(weighted_scores)
        distribution = Counter(labels)
        if average >= 0.15:
            overall_label = "positive"
        elif average <= -0.15:
            overall_label = "negative"
        else:
            overall_label = "neutral"
        return {
            "model": self.model_name,
            "article_count": len(analyzed),
            "sentiment_score": average,
            "confidence": sum(confidences) / len(confidences),
            "label": overall_label,
            "distribution": {key: distribution.get(key, 0) for key in ("positive", "neutral", "negative")},
            "articles": analyzed,
        }
