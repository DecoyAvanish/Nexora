from datetime import datetime
from flask import Blueprint,current_app,jsonify,request

regime_blueprint=Blueprint("regime",__name__)

@regime_blueprint.get("/regime")
def current_regime():
    text=request.args.get("as_of"); as_of=datetime.fromisoformat(text.replace("Z","+00:00")) if text else None
    return jsonify(current_app.extensions["market_regime"].classify(as_of))
