"""Financial-news sentiment routes."""

from flask import Blueprint, current_app, jsonify, request

from backend.services.market_data import normalize_symbol

sentiment_blueprint = Blueprint("sentiment", __name__)


@sentiment_blueprint.get("/sentiment/<symbol>")
def stock_sentiment(symbol: str):
    normalized = normalize_symbol(symbol)
    company_name = request.args.get("company")
    days = request.args.get("days", default=7, type=int) or 7
    articles = current_app.extensions["news"].company_news(
        normalized,
        company_name,
        days=days,
        limit=50,
    )
    result = current_app.extensions["sentiment"].analyze(articles)
    return jsonify({"symbol": normalized, "window_days": max(1, min(days, 90)), **result})
