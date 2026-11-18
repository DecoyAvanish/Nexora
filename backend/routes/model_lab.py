"""Public model transparency routes."""

from flask import Blueprint, current_app, jsonify

model_lab_blueprint = Blueprint("model_lab", __name__)


@model_lab_blueprint.get("/model-lab")
def model_lab():
    return jsonify(current_app.extensions["model_lab"].get_report())


@model_lab_blueprint.get("/model-lab/status")
def model_lab_status():
    return jsonify({"available": current_app.extensions["model_lab"].available})
