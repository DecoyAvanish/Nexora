"""News routes."""

from flask import Blueprint, current_app, jsonify, request

from backend.services.market_data import normalize_symbol

news_blueprint = Blueprint("news", __name__)


@news_blueprint.get("/news/<symbol>")
def company_news(symbol: str):
    normalized = normalize_symbol(symbol)
    days = request.args.get("days", default=7, type=int)
    limit = request.args.get("limit", default=25, type=int)
    company_name = request.args.get("company")
    articles = current_app.extensions["news"].company_news(
        normalized,
        company_name,
        days=days or 7,
        limit=limit or 25,
    )
    return jsonify({
        "symbol": normalized,
        "article_count": len(articles),
        "articles": [article.to_dict() for article in articles],
    })
