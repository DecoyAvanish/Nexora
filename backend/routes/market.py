"""Market search, quote, history, and prediction routes."""

from flask import Blueprint, current_app, jsonify, request
import time

from backend.services.market_data import normalize_symbol

market_blueprint = Blueprint("market", __name__)


def _observed_market_call(callback):
    started=time.monotonic();result=callback();observability=current_app.extensions.get("observability")
    if observability:observability.observe("provider:market_data",(time.monotonic()-started)*1000);observability.mark_freshness("market_data",metadata={"provider":"yfinance"})
    return result


@market_blueprint.get("/search")
def search():
    query = request.args.get("q", "")
    return jsonify({"result": _observed_market_call(lambda:current_app.extensions["market_data"].search(query))})


@market_blueprint.get("/search/<query>")
def legacy_search(query: str):
    return jsonify({"result": _observed_market_call(lambda:current_app.extensions["market_data"].search(query))})


@market_blueprint.get("/quote/<symbol>")
def quote(symbol: str):
    history = _observed_market_call(lambda:current_app.extensions["market_data"].history(normalize_symbol(symbol), period="5d"))
    return jsonify(current_app.extensions["market_data"].quote_payload(history))


@market_blueprint.get("/history/<symbol>")
def history(symbol: str):
    period = request.args.get("period", "6mo")
    if period not in {"1mo", "3mo", "6mo", "1y", "2y", "5y"}:
        from backend.errors import ApiError
        raise ApiError("Unsupported history period.", 400, "invalid_period")
    data = _observed_market_call(lambda:current_app.extensions["market_data"].history(normalize_symbol(symbol), period=period))
    return jsonify({"symbol": data.symbol, "chart_data": data.to_chart()})


@market_blueprint.get("/predict/<symbol>")
def predict(symbol: str):
    normalized = normalize_symbol(symbol)
    data = current_app.extensions["market_data"].history(normalized, period="6mo")
    prediction = current_app.extensions["prediction"].predict(data)
    previous = data.closes[-2] if len(data.closes) > 1 else data.last_price
    return jsonify({
        "symbol": normalized,
        "name": normalized,
        "last_price": data.last_price,
        "last_return": (data.last_price - previous) / previous if previous else 0,
        "open": data.opens[-1],
        "high": data.highs[-1],
        "low": data.lows[-1],
        "chart_data": data.to_chart(),
        **prediction,
    })
