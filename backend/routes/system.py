"""System and readiness endpoints."""

from flask import Blueprint, current_app, jsonify

system_blueprint = Blueprint("system", __name__)


@system_blueprint.get("/health")
def health():
    settings = current_app.config["SETTINGS"]
    return jsonify({
        "status": "ok",
        "service": "nexora-api",
        "environment": settings.environment,
        "market_data_configured": bool(settings.finnhub_api_key),
    })
