from backend.services.news import NewsArticle
from backend.services.sentiment import SentimentService


def fake_classifier(headlines, **kwargs):
    return [
        {"label": "positive", "score": 0.9},
        {"label": "negative", "score": 0.6},
    ]


def test_finbert_sentiment_is_confidence_weighted():
    articles = [
        NewsArticle("Profit rises", "https://example.com/1", "example.com", None, None, "English"),
        NewsArticle("Costs increase", "https://example.com/2", "example.com", None, None, "English"),
    ]
    result = SentimentService(classifier=fake_classifier).analyze(articles)
    assert round(result["sentiment_score"], 2) == 0.15
    assert result["label"] == "positive"
    assert result["distribution"] == {"positive": 1, "neutral": 0, "negative": 1}
