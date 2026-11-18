from backend.services.news import NewsService
import requests


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"articles": [{
            "title": "Apple launches a new product",
            "url": "https://example.com/apple",
            "domain": "example.com",
            "seendate": "20261117T150000Z",
            "sourcecountry": "United States",
            "language": "English",
        }]}


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.params = None

    def get(self, url, params, timeout):
        self.params = params
        return FakeResponse()


def test_company_news_maps_gdelt_articles():
    session = FakeSession()
    articles = NewsService(session=session).company_news("aapl", "Apple Inc", days=5)
    assert articles[0].title == "Apple launches a new product"
    assert articles[0].published_at == "2026-11-17T15:00:00+00:00"
    assert articles[0].provider == "gdelt"
    assert session.params["timespan"] == "5d"


class FallbackSession:
    def __init__(self):
        self.headers = {}
        self.calls = 0

    def get(self, url, params, timeout):
        self.calls += 1
        if self.calls == 1:
            raise requests.HTTPError("rate limited")
        response = FakeResponse()
        response.json = lambda: {"news": [
            {"title": "Apple reports record services revenue", "link": "https://example.com/apple-news", "publisher": "Reuters", "providerPublishTime": 1794960000},
            {"title": "Nvidia launches a new chip", "link": "https://example.com/nvidia", "publisher": "Reuters", "providerPublishTime": 1794960000},
        ]}
        return response


def test_yahoo_fallback_filters_unrelated_headlines():
    articles = NewsService(session=FallbackSession()).company_news("AAPL", "Apple Inc")
    assert len(articles) == 1
    assert articles[0].provider == "yahoo_finance"
    assert "Apple" in articles[0].title
