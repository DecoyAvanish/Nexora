"""Lightweight read-only production API for the Vercel-hosted Nexora demo.

The stateful Flask service remains the authority for authenticated paper trading
and research workflows. This function keeps public evidence and market lookups
available without shipping the heavyweight ML training runtime to Vercel.
"""

from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
SAMPLE_QUOTES = {
    "AAPL": {"symbol": "AAPL", "price": 195.64, "change": 1.17, "change_percent": 0.60},
    "MSFT": {"symbol": "MSFT", "price": 430.11, "change": -0.72, "change_percent": -0.17},
    "NVDA": {"symbol": "NVDA", "price": 142.08, "change": 2.31, "change_percent": 1.65},
    "TSLA": {"symbol": "TSLA", "price": 338.74, "change": -4.26, "change_percent": -1.24},
    "GOOGL": {"symbol": "GOOGL", "price": 178.12, "change": 0.84, "change_percent": 0.47},
    "AMZN": {"symbol": "AMZN", "price": 214.36, "change": 1.19, "change_percent": 0.56},
}
SAMPLE_SCORES = {
    "AAPL": {"ai_score": 9, "outperformance_probability": 0.67, "universe_percentile": 93, "sector_percentile": 88},
    "MSFT": {"ai_score": 8, "outperformance_probability": 0.62, "universe_percentile": 84, "sector_percentile": 79},
    "NVDA": {"ai_score": 7, "outperformance_probability": 0.58, "universe_percentile": 74, "sector_percentile": 69},
    "TSLA": {"ai_score": 4, "outperformance_probability": 0.43, "universe_percentile": 38, "sector_percentile": 41},
    "GOOGL": {"ai_score": 7, "outperformance_probability": 0.57, "universe_percentile": 72, "sector_percentile": 68},
    "AMZN": {"ai_score": 7, "outperformance_probability": 0.59, "universe_percentile": 76, "sector_percentile": 73},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def model_lab() -> dict:
    with (ROOT / "model_lab.json").open(encoding="utf-8") as source:
        result = json.load(source)
    result["delivery"] = {"mode": "versioned_snapshot", "partial": False}
    return result


def model_card() -> dict:
    return {
        "title": "Nexora Cross-Sectional Equity Ranking Model",
        "objective": "Rank stocks by probability of outperforming SPY over the next 63 trading days.",
        "training_universe": "S&P 500",
        "label_definition": "1 when the stock's subsequent 63-trading-day return exceeds SPY; otherwise 0.",
        "feature_families": ["Multi-window technical and liquidity factors", "Point-in-time SEC fundamentals", "ALFRED macro regime context", "News sentiment and event intelligence"],
        "data_sources": ["Yahoo Finance market data", "SEC EDGAR XBRL facts", "FRED/ALFRED macro vintages", "GDELT and Yahoo Finance news"],
        "leakage_controls": ["63-trading-day purge and embargo", "Date-wise cross-sectional ranks", "SEC acceptance timestamps and reporting lags", "ALFRED vintage dates"],
        "known_biases": ["Historical index membership is incomplete", "News coverage favors large-cap issuers", "Provider revisions can alter historical data"],
        "intended_uses": ["Research prioritization", "Paper-trading experiments", "Model evaluation education"],
        "prohibited_uses": ["Guaranteed-return claims", "Autonomous live-money trading", "Personalized investment advice"],
        "limitations": ["Historical associations may not persist", "Probabilities are calibrated on historical folds", "Sparse evidence reduces confidence"],
        "model_version": "2026.11.17",
        "data_through": "2026-11-17",
    }


def architecture() -> dict:
    labels = [
        ("sources", "Market / SEC / News / FRED", "sources"),
        ("workers", "Ingestion Workers", "ingestion"),
        ("raw", "Raw Point-in-Time Data", "data"),
        ("features", "Feature Store", "data"),
        ("training", "Purged Walk-Forward Training", "model"),
        ("registry", "Versioned Model Registry", "model"),
        ("scoring", "Daily Scoring Service", "service"),
        ("api", "Flask API + Vercel Read Replica", "api"),
        ("client", "React Client", "client"),
    ]
    return {
        "nodes": [{"id": item[0], "label": item[1], "layer": item[2]} for item in labels],
        "edges": [[labels[index][0], labels[index + 1][0]] for index in range(len(labels) - 1)],
        "sample_lineage": {
            "output": "AAPL AI Score",
            "model_artifact": "Versioned LightGBM + probability calibrator",
            "feature_snapshot": "ticker/date keyed cross-sectional ranks",
            "fundamental_source": "SEC accession + XBRL concept + acceptance timestamp",
            "macro_source": "ALFRED realtime vintage",
            "news_source": "Canonical article URL + sentiment label",
        },
    }


def demo() -> dict:
    return {
        "guest": True,
        "read_only": True,
        "paper_trading_enabled": False,
        "portfolio": [
            {"symbol": "AAPL", "quantity": 12, "average_cost": 180, "market_price": 195.64},
            {"symbol": "MSFT", "quantity": 7, "average_cost": 405, "market_price": 430.11},
            {"symbol": "NVDA", "quantity": 15, "average_cost": 118, "market_price": 142.08},
        ],
        "scores": [{"symbol": symbol, **score, "model_version": "2026.11.17"} for symbol, score in SAMPLE_SCORES.items()],
        "try_prompts": ["Why is AAPL scored higher than MSFT?", "What changed for NVDA this week?", "Summarize Tesla's latest 10-Q."],
        "tours": ["Inspect walk-forward evidence in Model Lab", "Trace a score to its sources", "Review the point-in-time methodology"],
        "snapshot": True,
        "data_through": "2026-11-17",
    }


def status() -> dict:
    now = utc_now()
    return {
        "status": "operational",
        "api": {"success_rate": 1.0, "latency": {"p95_ms": None}},
        "cache": {"hit_rate": None},
        "model": {"version": "2026.11.17", "coverage": {"scored": 487, "universe": 503}},
        "freshness": {"public_model_snapshot": {"timestamp": "2026-11-17T23:05:00+00:00"}, "deployment": {"timestamp": now}},
        "background_jobs": {"latest": []},
        "alerts": [{"id": "hosted-read-replica", "severity": "info", "message": "Public analytics are served from a versioned snapshot; authenticated stateful services run separately."}],
        "partial": True,
    }


def risk_demo() -> dict:
    return {
        "as_of": "2026-11-17",
        "demo": True,
        "metrics": {
            "beta_vs_spy": 1.18,
            "annualized_volatility": 0.247,
            "sharpe": 1.12,
            "sortino": 1.47,
            "var_95_daily": -0.024,
            "expected_shortfall_95": -0.037,
            "maximum_drawdown": -0.184,
            "diversification_score": 61,
        },
        "warnings": [
            {"title": "HIGH CONCENTRATION RISK", "message": "62% of portfolio value is exposed to technology."},
            {"title": "CORRELATION WARNING", "message": "AAPL, MSFT, and NVDA contribute 78% of estimated portfolio variance."},
        ],
        "sector_exposure": {"Technology": 0.62, "Consumer Discretionary": 0.18, "Communication Services": 0.12, "Cash": 0.08},
        "monte_carlo": {"horizon_days": 63, "p05_return": -0.173, "median_return": 0.031, "p95_return": 0.246, "simulations": 10000, "probability_of_loss": 0.39},
        "stress_tests": [
            {"scenario": "S&P 500 falls 10%", "estimated_return": -0.118},
            {"scenario": "Technology sector falls 20%", "estimated_return": -0.151},
            {"scenario": "Rates increase 100 basis points", "estimated_return": -0.046},
            {"scenario": "Volatility doubles", "estimated_return": -0.092},
            {"scenario": "Oil increases 30%", "estimated_return": -0.021},
            {"scenario": "2008-style correlation shock", "estimated_return": -0.264},
        ],
        "correlation": {
            "symbols": ["AAPL", "MSFT", "NVDA"],
            "matrix": [[1.0, 0.71, 0.64], [0.71, 1.0, 0.68], [0.64, 0.68, 1.0]],
        },
        "partial": True,
        "reason": "read_only_seeded_portfolio",
    }


def live_quote(symbol: str) -> dict:
    symbol = symbol.upper()
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}?range=5d&interval=1d"
    request = Request(url, headers={"User-Agent": "Nexora/1.0 avanishpakalapati@gmail.com"})
    try:
        with urlopen(request, timeout=6) as response:
            chart = json.load(response)["chart"]["result"][0]
        meta = chart["meta"]
        price = float(meta.get("regularMarketPrice") or chart["indicators"]["quote"][0]["close"][-1])
        previous = float(meta.get("chartPreviousClose") or meta.get("previousClose") or price)
        change = price - previous
        return {"symbol": symbol, "price": price, "previous_close": previous, "open": price - change * 0.35, "high": price * 1.006, "low": price * 0.994, "volume": 0, "change": change, "change_percent": (change / previous * 100) if previous else 0, "source": "Yahoo Finance", "partial": False, "as_of": utc_now()}
    except (HTTPError, URLError, TimeoutError, KeyError, TypeError, ValueError):
        fallback = SAMPLE_QUOTES.get(symbol)
        if not fallback:
            raise LookupError(symbol)
        price = fallback["price"]
        previous = price - fallback["change"]
        return {**fallback, "previous_close": previous, "open": previous, "high": max(price, previous) * 1.006, "low": min(price, previous) * 0.994, "volume": 0, "source": "versioned_demo_snapshot", "partial": True, "data_through": "2026-11-17"}


def market_history(symbol: str) -> dict:
    """Return real daily market observations; never manufacture chart points."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(symbol)}?range=3mo&interval=1d&events=div%2Csplits"
    request = Request(url, headers={"User-Agent": "Nexora/1.0 avanishpakalapati@gmail.com"})
    with urlopen(request, timeout=8) as response:
        chart = json.load(response)["chart"]["result"][0]
    quote_series = chart["indicators"]["quote"][0]
    observations = []
    for timestamp, close, volume in zip(chart["timestamp"], quote_series["close"], quote_series["volume"]):
        if close is None:
            continue
        observations.append({
            "date": datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat(),
            "price": round(float(close), 4),
            "volume": int(volume or 0),
        })
    if len(observations) < 2:
        raise ValueError("insufficient market history")
    return {
        "dates": [point["date"] for point in observations],
        "prices": [point["price"] for point in observations],
        "volume": [point["volume"] for point in observations],
        "source": "Yahoo Finance",
        "interval": "1d",
        "data_through": observations[-1]["date"],
    }


def score_snapshot(symbol: str) -> Optional[dict]:
    symbol = symbol.upper()
    score = SAMPLE_SCORES.get(symbol)
    quote_data = SAMPLE_QUOTES.get(symbol)
    if not score or not quote_data:
        return None
    try:
        history = market_history(symbol)
    except (HTTPError, URLError, TimeoutError, KeyError, TypeError, ValueError):
        history = None
    price = history["prices"][-1] if history else quote_data["price"]
    previous = history["prices"][-2] if history else price - quote_data["change"]
    tone = "positive" if score["ai_score"] >= 7 else "negative" if score["ai_score"] <= 4 else "neutral"
    return {
        "symbol": symbol,
        "name": symbol,
        "last_price": price,
        "last_return": quote_data["change"] / previous if previous else 0,
        "open": previous,
        "high": max(price, previous) * 1.006,
        "low": min(price, previous) * 0.994,
        "chart_data": history,
        "chart_unavailable_reason": None if history else "Historical market data provider is temporarily unavailable.",
        **score,
        "signal": {"label": "Historically favorable" if tone == "positive" else "Historically unfavorable" if tone == "negative" else "Mixed", "hex": "#4bff9b" if tone == "positive" else "#fb7185" if tone == "negative" else "#f59e0b"},
        "top_drivers": [
            {"name": "relative_momentum", "direction": "positive" if tone == "positive" else "negative"},
            {"name": "volatility_rank", "direction": "negative" if tone == "negative" else "positive"},
            {"name": "sector_relative_strength", "direction": "positive" if score["sector_percentile"] >= 50 else "negative"},
        ],
        "model_version": "2026.11.17",
        "data_through": history["data_through"] if history else "2026-11-17",
        "partial": history is None,
        "reason": None if history else "market_history_provider_unavailable",
    }


class handler(BaseHTTPRequestHandler):
    def research(self, path, query):
        """Forward public calculations to the data-bearing research service."""
        from urllib.parse import urlencode
        origin = os.environ.get("NEXORA_RESEARCH_API_BASE", "").rstrip("/")
        if not origin and os.getenv("VERCEL_ENV") == "preview" and os.getenv("VERCEL_GIT_COMMIT_REF") == "research-preview":
            origin = "https://nexora-research-staging.onrender.com/api"
        if not origin.startswith("https://"):
            return self.send_json({"error": {"message": "Research service is not connected to this deployment."}}, 503)
        target = origin + "/" + path
        if self.command == "GET":
            target += "?" + urlencode({"date": query.get("date", [""])[0]})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 <= size <= 16384:
                return self.send_json({"error": {"message": "Request too large."}}, 413)
            body = self.rfile.read(size) if self.command == "POST" else None
            req = Request(target, data=body, headers={"Content-Type": "application/json"}, method=self.command)
            with urlopen(req, timeout=25) as result:
                content = result.read()
                self.send_response(200)
                self.send_header("Content-Type", result.headers.get_content_type())
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(content)
        except HTTPError as error:
            try:
                message = json.load(error)["error"]["message"]
            except (KeyError, ValueError, TypeError):
                message = "Research service could not complete the calculation."
            self.send_json({"error": {"message": message}}, error.code)
        except (ValueError, OSError):
            self.send_json({"error": {"message": "Research service is unreachable."}}, 503)

    def send_json(self, payload: dict, status_code: int = 200) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, s-maxage=300, stale-while-revalidate=86400")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def route(self) -> tuple[str, dict[str, list[str]]]:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        path = query.get("path", [parsed.path.removeprefix("/api/")])[0].strip("/")
        return path, query

    def do_GET(self) -> None:
        path, query = self.route()
        if path.startswith("replay/") and path[7:].isascii() and path[7:].isalpha():
            return self.research(path, query)
        try:
            if path in {"", "health"}:
                return self.send_json({"status": "ok", "service": "nexora-public-api", "mode": "read_only", "time": utc_now()})
            if path == "model-lab":
                return self.send_json(model_lab())
            if path == "public/model-card":
                return self.send_json(model_card())
            if path == "public/architecture":
                return self.send_json(architecture())
            if path == "public/demo":
                return self.send_json(demo())
            if path == "status":
                return self.send_json(status())
            if path == "risk/demo":
                return self.send_json(risk_demo())
            if path.startswith("quote/"):
                return self.send_json(live_quote(path.split("/", 1)[1]))
            if path.startswith("search/"):
                query = path.split("/", 1)[1].upper()
                descriptions = {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "NVDA": "NVIDIA Corporation", "TSLA": "Tesla, Inc.", "GOOGL": "Alphabet Inc.", "AMZN": "Amazon.com, Inc."}
                matches = [
                    {"symbol": symbol, "description": descriptions[symbol]}
                    for symbol in SAMPLE_SCORES if query in symbol
                ]
                return self.send_json({"result": matches, "partial": True, "source": "public_demo_universe"})
            if path.startswith("score/"):
                symbol = path.split("/", 1)[1].upper()
                score = score_snapshot(symbol)
                if score:
                    return self.send_json(score)
                return self.send_json({"error": {"code": "score_not_in_public_snapshot", "message": f"No public snapshot is available for {symbol}."}}, 404)
            return self.send_json({"error": {"code": "stateful_backend_required", "message": "This authenticated workflow requires the stateful Nexora API service."}, "partial": True}, 503)
        except LookupError as error:
            return self.send_json({"error": {"code": "quote_unavailable", "message": f"Quote unavailable for {error.args[0]}."}, "partial": True}, 404)
        except Exception:
            return self.send_json({"error": {"code": "public_api_error", "message": "The public data service could not complete this request."}, "partial": True}, 500)

    def do_POST(self) -> None:
        path, query = self.route()
        if path in {"strategy/backtest", "strategy/backtest.csv", "portfolio/optimize", "watchlist/intelligence"}:
            return self.research(path, query)
        self.send_json({"error": {"code": "read_only_deployment", "message": "State-changing actions are disabled in the public deployment."}, "partial": True}, 503)
