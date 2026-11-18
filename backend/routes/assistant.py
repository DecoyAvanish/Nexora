from flask import Blueprint,current_app,jsonify,request
from backend.errors import ApiError
assistant_blueprint=Blueprint("assistant",__name__)
@assistant_blueprint.post("/research-assistant")
def answer():
    user=None
    if request.headers.get("Authorization"):
        try:user=current_app.extensions["identity"].user_id(request)
        except ApiError:pass
    return jsonify(current_app.extensions["research_assistant"].answer((request.get_json(silent=True) or {}).get("question",""),user))
