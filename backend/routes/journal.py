from flask import Blueprint,current_app,jsonify,request
journal_blueprint=Blueprint("journal",__name__)
def user():return current_app.extensions["identity"].user_id(request)
@journal_blueprint.post("/journal")
def create():return jsonify(current_app.extensions["research_journal"].create(user(),request.get_json(silent=True) or {})),201
@journal_blueprint.get("/journal")
def entries():return jsonify({"entries":current_app.extensions["research_journal"].list(user())})
@journal_blueprint.post("/journal/<entry_id>/close")
def close(entry_id):return jsonify(current_app.extensions["research_journal"].close(user(),entry_id,request.get_json(silent=True) or {}))
@journal_blueprint.get("/journal/analytics")
def analytics():return jsonify(current_app.extensions["research_journal"].analytics(user()))
