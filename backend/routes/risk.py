from flask import Blueprint, current_app, jsonify, request

risk_blueprint=Blueprint("risk",__name__)

@risk_blueprint.get("/risk/portfolio")
def portfolio_risk():
    user=current_app.extensions["identity"].user_id(request)
    return jsonify(current_app.extensions["portfolio_risk"].analyze(user,request.args.get("simulations",5000,type=int),request.args.get("horizon_days",63,type=int)))
