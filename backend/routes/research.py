import csv,io
from flask import Blueprint,current_app,jsonify,request,Response

research_blueprint=Blueprint("research",__name__)

@research_blueprint.get("/replay/<symbol>")
def replay(symbol):return jsonify(current_app.extensions["historical_research"].replay(symbol,request.args["date"]))

@research_blueprint.post("/strategy/backtest")
def backtest():return jsonify(current_app.extensions["historical_research"].backtest(request.get_json(silent=True) or {}))

@research_blueprint.post("/strategy/backtest.csv")
def backtest_csv():
    result=current_app.extensions["historical_research"].backtest(request.get_json(silent=True) or {}); output=io.StringIO(); fields=["date","ticker","sector","weight","ai_score","probability"]; writer=csv.DictWriter(output,fieldnames=fields);writer.writeheader();writer.writerows(result["trades"])
    return Response(output.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=nexora-backtest-trades.csv"})

@research_blueprint.post("/portfolio/optimize")
def optimize():
    body=request.get_json(silent=True) or {};return jsonify(current_app.extensions["portfolio_optimization"].optimize(body.get("symbols",[]),body.get("mode","equal_weight"),float(body.get("sector_limit",.4)),int(body.get("simulations",4000))))

@research_blueprint.post("/watchlist/intelligence")
def watchlist():
    body=request.get_json(silent=True) or {};return jsonify(current_app.extensions["watchlist_intelligence"].monitor(body.get("symbols",[]),body.get("company_names")))
