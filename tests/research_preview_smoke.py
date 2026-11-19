"""Run against a Nexora preview with: python tests/research_preview_smoke.py PREVIEW_URL"""
import csv
import io
import json
import sys
from urllib.request import Request, urlopen


def check_preview(base):
    def request(path, payload=None, csv_response=False):
        body = None if payload is None else json.dumps(payload).encode()
        req = Request(base.rstrip("/") + "/api/" + path, data=body,
                      headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=90) as response:
            if csv_response:
                assert response.headers.get_content_type() == "text/csv"
                return list(csv.DictReader(io.StringIO(response.read().decode())))
            return json.load(response)

    replay = request("replay/AAPL?date=2025-06-30")
    assert replay["symbol"] == "AAPL" and replay["score_date"] <= "2025-06-30"
    assert 1 <= replay["score"] <= 10
    strategy = {"conditions": [{"field": "ai_score", "operator": ">=", "value": 8}]}
    backtest = request("strategy/backtest", strategy)
    trades = request("strategy/backtest.csv", strategy, csv_response=True)
    assert trades and len(trades) == len(backtest["trades"])
    assert all(float(row["ai_score"]) >= 8 for row in trades)
    symbols = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]
    result = request("portfolio/optimize", {"symbols": symbols, "mode": "maximum_sharpe"})
    assert abs(sum(item["weight"] for item in result["allocation"]) - 1) < .001
    scan = request("watchlist/intelligence", {"symbols": symbols})
    assert set(scan["symbols"]) == set(symbols) and scan["alert_count"] == len(scan["alerts"])
    print("All five Research preview checks passed.")


if __name__ == "__main__":
    check_preview(sys.argv[1])
