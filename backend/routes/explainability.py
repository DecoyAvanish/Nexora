from flask import Blueprint,current_app,jsonify,request

explainability_blueprint=Blueprint("explainability",__name__)

@explainability_blueprint.get("/explain/<symbol>")
def explain(symbol):return jsonify(current_app.extensions["explainability"].explain(symbol,request.args.get("company")))
