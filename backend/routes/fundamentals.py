"""SEC filing and point-in-time fundamental routes."""

from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

fundamentals_blueprint = Blueprint("fundamentals", __name__)


@fundamentals_blueprint.get("/fundamentals/<symbol>/filings")
def recent_filings(symbol: str):
    limit = request.args.get("limit", default=25, type=int) or 25
    return jsonify(current_app.extensions["sec_edgar"].recent_filings(symbol, limit))


@fundamentals_blueprint.get("/fundamentals/<symbol>/facts")
def point_in_time_facts(symbol: str):
    as_of_text = request.args.get("as_of")
    as_of = datetime.fromisoformat(as_of_text.replace("Z", "+00:00")) if as_of_text else None
    result = current_app.extensions["sec_edgar"].point_in_time_facts(symbol, as_of)
    return jsonify({**result, "observations": [observation.to_dict() for observation in result["observations"]]})
