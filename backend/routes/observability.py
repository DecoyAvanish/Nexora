from flask import Blueprint,current_app,jsonify
observability_blueprint=Blueprint("observability",__name__)
@observability_blueprint.get("/status")
def status():return jsonify(current_app.extensions["observability"].status(current_app.extensions.get("pipeline"),current_app.extensions.get("cross_sectional")))
