from flask import Blueprint,current_app,jsonify,request

news_intelligence_blueprint=Blueprint("news_intelligence",__name__)

@news_intelligence_blueprint.get("/news-intelligence/<symbol>")
def intelligence(symbol):
    return jsonify(current_app.extensions["news_intelligence"].analyze(symbol,request.args.get("company"),request.args.get("days",14,type=int),request.args.get("limit",75,type=int)))
