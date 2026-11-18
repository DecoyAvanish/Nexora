"""Flask application factory for the Nexora API."""

from __future__ import annotations

from flask import Flask, jsonify
from flask_cors import CORS

from .config import Settings
from .errors import register_error_handlers
from .routes.market import market_blueprint
from .routes.news import news_blueprint
from .routes.sentiment import sentiment_blueprint
from .routes.scoring import scoring_blueprint
from .routes.model_lab import model_lab_blueprint
from .routes.fundamentals import fundamentals_blueprint
from .routes.system import system_blueprint
from .services.market_data import MarketDataService
from .services.news import NewsService
from .services.sentiment import SentimentService
from .services.scoring import StockScoringService
from .services.cross_sectional import CrossSectionalScoreService
from .services.model_lab import ModelLabService
from .services.sec_edgar import SecEdgarService
from .services.prediction import PredictionService


def create_app(settings: Settings | None = None, *, market_data=None, prediction=None, news=None, sentiment=None, scoring=None, cross_sectional=None, model_lab=None, sec_edgar=None) -> Flask:
    app = Flask(__name__)
    resolved_settings = settings or Settings.from_env()
    app.config["SETTINGS"] = resolved_settings
    CORS(app, resources={r"/api/*": {"origins": list(resolved_settings.allowed_origins)}})
    app.extensions["market_data"] = market_data or MarketDataService(resolved_settings.request_timeout_seconds)
    app.extensions["prediction"] = prediction or PredictionService()
    app.extensions["news"] = news or NewsService(resolved_settings.request_timeout_seconds)
    app.extensions["sentiment"] = sentiment or SentimentService()
    app.extensions["scoring"] = scoring or StockScoringService()
    app.extensions["cross_sectional"] = cross_sectional or CrossSectionalScoreService(resolved_settings.model_artifact_root)
    app.extensions["model_lab"] = model_lab or ModelLabService(resolved_settings.model_artifact_root)
    app.extensions["sec_edgar"] = sec_edgar or SecEdgarService(resolved_settings.sec_user_agent, resolved_settings.request_timeout_seconds, reporting_lag_hours=resolved_settings.sec_reporting_lag_hours)
    app.register_blueprint(system_blueprint, url_prefix="/api")
    app.register_blueprint(market_blueprint, url_prefix="/api")
    app.register_blueprint(news_blueprint, url_prefix="/api")
    app.register_blueprint(sentiment_blueprint, url_prefix="/api")
    app.register_blueprint(scoring_blueprint, url_prefix="/api")
    app.register_blueprint(model_lab_blueprint, url_prefix="/api")
    app.register_blueprint(fundamentals_blueprint, url_prefix="/api")

    @app.get("/")
    def index():
        return jsonify({"service": "nexora-api", "health": "/api/health"})

    register_error_handlers(app)
    return app


def main() -> None:
    settings = Settings.from_env()
    app = create_app(settings)
    app.run(host=settings.host, port=settings.port, debug=settings.environment == "development")


if __name__ == "__main__":
    main()
