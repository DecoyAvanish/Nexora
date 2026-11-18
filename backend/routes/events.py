from flask import Blueprint,current_app,jsonify,request
from backend.errors import ApiError

events_blueprint=Blueprint("events",__name__)

def _optional_user():
    if not request.headers.get("Authorization"):return None
    try:return current_app.extensions["identity"].user_id(request)
    except ApiError:return None

@events_blueprint.get("/events/<symbol>")
def timeline(symbol):
    result=current_app.extensions["event_intelligence"].timeline(symbol,request.args.get("company"),request.args.get("days",30,type=int),_optional_user())
    return jsonify(result)

@events_blueprint.get("/events/<symbol>/explain")
def explain(symbol):
    result=current_app.extensions["event_intelligence"].explain_score_change(symbol,request.args.get("company"),request.args.get("days",30,type=int),_optional_user())
    return jsonify(result)
