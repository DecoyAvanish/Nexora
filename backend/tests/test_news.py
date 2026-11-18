from backend.services.news import NewsService


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
    assert session.params["timespan"] == "5d"
