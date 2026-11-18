from backend.app import create_app
from backend.services.market_data import MarketHistory, normalize_symbol


class FakeMarketData:
    def search(self, query):
        return [{"symbol": "AAPL", "description": "Apple Inc."}]

    def history(self, symbol, period="6mo"):
        return MarketHistory(symbol.upper(), ["2026-01-01", "2026-01-02"], [99, 100], [101, 103], [98, 99], [100, 102], [1000, 1200])

    def quote_payload(self, history):
        return {"symbol": history.symbol, "price": history.last_price}


class FakePrediction:
    artifacts_available = True

    def predict(self, history):
        return {"predicted_return": 0.01, "predicted_price": 103.02, "confidence": 0.8, "model": "test"}


def test_symbol_validation():
    assert normalize_symbol(" aapl ") == "AAPL"


def test_market_routes(settings):
    client = create_app(settings, market_data=FakeMarketData(), prediction=FakePrediction()).test_client()
    assert client.get("/api/search?q=apple").get_json()["result"][0]["symbol"] == "AAPL"
    assert client.get("/api/quote/aapl").get_json() == {"symbol": "AAPL", "price": 102}
    prediction = client.get("/api/predict/aapl")
    assert prediction.status_code == 200
    assert prediction.get_json()["predicted_price"] == 103.02
