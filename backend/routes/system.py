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
        "prediction_artifacts_available": current_app.extensions["prediction"].artifacts_available,
        "cross_sectional_model_available": current_app.extensions["cross_sectional"].available,
        "model_lab_available": current_app.extensions["model_lab"].available,
    })
