"""Explainable AI stock score routes."""

from flask import Blueprint, current_app, jsonify, request

from backend.services.market_data import normalize_symbol

scoring_blueprint = Blueprint("scoring", __name__)


@scoring_blueprint.get("/score/<symbol>")
def score_stock(symbol: str):
    normalized = normalize_symbol(symbol)
    company_name = request.args.get("company")
    history = current_app.extensions["market_data"].history(normalized, period="1y")
    articles = current_app.extensions["news"].company_news(normalized, company_name, days=14, limit=50)
    sentiment = current_app.extensions["sentiment"].analyze(articles)
    score = current_app.extensions["scoring"].score(history, sentiment)
    previous = history.closes[-2] if len(history.closes) > 1 else history.last_price
    return jsonify({
        "symbol": normalized,
        "name": company_name or normalized,
        "last_price": history.last_price,
        "last_return": (history.last_price - previous) / previous if previous else 0,
        "open": history.opens[-1],
        "high": history.highs[-1],
        "low": history.lows[-1],
        "chart_data": history.to_chart(),
        "sentiment": sentiment,
        **score,
    })
