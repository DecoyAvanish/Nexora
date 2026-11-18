"""Validated market-data access without fabricated fallback prices."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

from backend.errors import ApiError

SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


def normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(symbol):
        raise ApiError("Enter a valid stock symbol.", 400, "invalid_symbol")
    return symbol


@dataclass(frozen=True)
class MarketHistory:
    symbol: str
    dates: list[str]
    opens: list[float]
    highs: list[float]
    lows: list[float]
    closes: list[float]
    volumes: list[int]

    @property
    def last_price(self) -> float:
        return self.closes[-1]

    def to_chart(self) -> dict[str, Any]:
        return {"dates": self.dates, "prices": self.closes, "volume": self.volumes}


class MarketDataService:
    def __init__(self, timeout_seconds: float = 10, session: requests.Session | None = None):
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "Nexora/1.0"})

    def search(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        cleaned = query.strip()
        if len(cleaned) < 1 or len(cleaned) > 80:
            raise ApiError("Search query must be between 1 and 80 characters.", 400, "invalid_query")

        try:
            response = self.session.get(
                "https://query1.finance.yahoo.com/v1/finance/search",
                params={"q": cleaned, "quotesCount": limit, "newsCount": 0},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise ApiError("Market search is temporarily unavailable.", 503, "market_data_unavailable") from error

        results = []
        for quote in response.json().get("quotes", []):
            symbol = str(quote.get("symbol", "")).upper()
            if quote.get("quoteType") not in {"EQUITY", "ETF"} or not SYMBOL_PATTERN.fullmatch(symbol):
                continue
            results.append({
                "symbol": symbol,
                "description": quote.get("longname") or quote.get("shortname") or symbol,
                "exchange": quote.get("exchange") or "",
                "type": quote.get("quoteType", "").lower(),
            })
        return results[:limit]

    def history(self, raw_symbol: str, period: str = "6mo") -> MarketHistory:
        symbol = normalize_symbol(raw_symbol)
        try:
            import yfinance as yf

            frame = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=False, timeout=self.timeout_seconds)
        except Exception as error:
            raise ApiError("Market history is temporarily unavailable.", 503, "market_data_unavailable") from error

        if frame is None or frame.empty:
            raise ApiError(f"No market data was found for {symbol}.", 404, "symbol_not_found")

        required = ("Open", "High", "Low", "Close", "Volume")
        if any(column not in frame for column in required):
            raise ApiError("The market provider returned incomplete data.", 502, "invalid_market_data")

        frame = frame.dropna(subset=list(required))
        if frame.empty:
            raise ApiError(f"No usable market data was found for {symbol}.", 404, "symbol_not_found")

        dates = [index.strftime("%Y-%m-%d") for index in frame.index]
        return MarketHistory(
            symbol=symbol,
            dates=dates,
            opens=[float(value) for value in frame["Open"].tolist()],
            highs=[float(value) for value in frame["High"].tolist()],
            lows=[float(value) for value in frame["Low"].tolist()],
            closes=[float(value) for value in frame["Close"].tolist()],
            volumes=[int(value) for value in frame["Volume"].tolist()],
        )

    @staticmethod
    def quote_payload(history: MarketHistory) -> dict[str, Any]:
        previous = history.closes[-2] if len(history.closes) > 1 else history.last_price
        change = history.last_price - previous
        change_percent = (change / previous * 100) if previous else 0.0
        return {
            "symbol": history.symbol,
            "price": history.last_price,
            "previous_close": previous,
            "change": change,
            "change_percent": change_percent,
            "open": history.opens[-1],
            "high": history.highs[-1],
            "low": history.lows[-1],
            "volume": history.volumes[-1],
            "as_of": datetime.now(timezone.utc).isoformat(),
        }
