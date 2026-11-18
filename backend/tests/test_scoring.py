from backend.services.market_data import MarketHistory
from backend.services.scoring import StockScoringService


def test_positive_trend_and_news_produce_green_score():
    prices = [100 + index * 0.5 for index in range(260)]
    history = MarketHistory(
        "TEST",
        [f"day-{index}" for index in range(260)],
        prices,
        [price + 1 for price in prices],
        [price - 1 for price in prices],
        prices,
        [1_000_000 + index * 100 for index in range(260)],
    )
    sentiment = {"sentiment_score": 0.8, "article_count": 12}
    result = StockScoringService().score(history, sentiment)
    assert result["ai_score"] >= 7
    assert result["signal"]["color"] == "green"
    assert result["top_drivers"]
