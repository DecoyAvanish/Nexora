from flask import Blueprint,current_app,jsonify,request
pipeline_blueprint=Blueprint("pipeline",__name__)
@pipeline_blueprint.get("/pipeline")
def dashboard():current_app.extensions["identity"].user_id(request);return jsonify(current_app.extensions["pipeline"].dashboard())
@pipeline_blueprint.post("/pipeline/<job_name>/run")
def run(job_name):current_app.extensions["identity"].user_id(request);return jsonify(current_app.extensions["pipeline"].run(job_name,request.get_json(silent=True) or {}))
