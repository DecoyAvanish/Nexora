"""Explainable AI stock score routes."""

from flask import Blueprint, current_app, jsonify, request
import time

from backend.services.market_data import normalize_symbol
from backend.errors import ApiError

scoring_blueprint = Blueprint("scoring", __name__)


@scoring_blueprint.get("/score/<symbol>")
def score_stock(symbol: str):
    inference_started=time.monotonic()
    normalized = normalize_symbol(symbol)
    company_name = request.args.get("company")
    history = current_app.extensions["market_data"].history(normalized, period="1y")
    cross_sectional = current_app.extensions["cross_sectional"]
    if cross_sectional.available:
        score = cross_sectional.get_score(normalized)
        sentiment = None
        score_source = "production_cross_sectional_model"
    else:
        partial=False;missing=[];partial_reason=None
        try:
            articles = current_app.extensions["news"].company_news(normalized, company_name, days=14, limit=50)
            sentiment = current_app.extensions["sentiment"].analyze(articles)
        except ApiError as error:
            sentiment={"sentiment_score":0,"article_count":0,"label":"unavailable","confidence":0,"articles":[]};partial=True;missing=["sentiment"];partial_reason=error.code
        score = current_app.extensions["scoring"].score(history, sentiment)
        score.update({
            "outperformance_probability": None,
            "universe_percentile": None,
            "sector_percentile": None,
            "model_version": None,
            "data_through": history.dates[-1],
            "model_type": "technical_sentiment_fallback",
            "partial":partial,
            "missing_components":missing,
            "reason":partial_reason,
        })
        score_source = "fallback_composite"
    previous = history.closes[-2] if len(history.closes) > 1 else history.last_price
    try:
        adjustment = current_app.extensions["market_regime"].adjust_score(score, history)
        score["ai_score"] = adjustment.pop("display_score")
        score["signal"] = current_app.extensions["scoring"]._signal(score["ai_score"])
        score["regime_adjustment"] = adjustment
    except ApiError as error:
        score["regime_adjustment"] = {"status":"unavailable","reason":error.code}
    current_app.extensions["score_history"].record(normalized,score)
    response=jsonify({
        "symbol": normalized,
        "name": company_name or normalized,
        "last_price": history.last_price,
        "last_return": (history.last_price - previous) / previous if previous else 0,
        "open": history.opens[-1],
        "high": history.highs[-1],
        "low": history.lows[-1],
        "chart_data": history.to_chart(),
        "sentiment": sentiment,
        "score_source": score_source,
        **score,
    })
    current_app.extensions["observability"].observe("model_inference",(time.monotonic()-inference_started)*1000)
    current_app.extensions["observability"].mark_freshness("model_score",score.get("data_through"),{"symbol":normalized,"model_version":score.get("model_version")})
    return response
