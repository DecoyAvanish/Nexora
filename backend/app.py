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
from .routes.paper_trading import paper_blueprint
from .routes.risk import risk_blueprint
from .routes.regime import regime_blueprint
from .routes.events import events_blueprint
from .routes.news_intelligence import news_intelligence_blueprint
from .routes.system import system_blueprint
from .services.market_data import MarketDataService
from .services.news import NewsService
from .services.sentiment import SentimentService
from .services.scoring import StockScoringService
from .services.cross_sectional import CrossSectionalScoreService
from .services.model_lab import ModelLabService
from .services.sec_edgar import SecEdgarService
from .services.fundamental_analysis import FundamentalAnalysisService
from .services.auth import IdentityService
from .services.paper_execution import PaperExecutionService
from .services.portfolio_risk import PortfolioRiskService
from .services.fred import FredService
from .services.market_regime import MarketRegimeService
from .services.score_history import ScoreHistoryService
from .services.event_intelligence import EventIntelligenceService
from .services.news_intelligence import NewsIntelligenceService
from .services.prediction import PredictionService


def create_app(settings: Settings | None = None, *, market_data=None, prediction=None, news=None, sentiment=None, scoring=None, cross_sectional=None, model_lab=None, sec_edgar=None, fundamental_analysis=None, identity=None, paper_execution=None, fred=None, market_regime=None) -> Flask:
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
    app.extensions["fundamental_analysis"] = fundamental_analysis or FundamentalAnalysisService(app.extensions["sec_edgar"], app.extensions["market_data"])
    app.extensions["identity"] = identity or IdentityService(resolved_settings.firebase_web_api_key, resolved_settings.environment, resolved_settings.request_timeout_seconds)
    app.extensions["paper_execution"] = paper_execution or PaperExecutionService(resolved_settings.paper_db_path, app.extensions["market_data"], resolved_settings.paper_starting_cash, resolved_settings.paper_slippage_bps, resolved_settings.paper_commission)
    app.extensions["portfolio_risk"] = PortfolioRiskService(app.extensions["paper_execution"], app.extensions["market_data"])
    app.extensions["fred"] = fred or FredService(resolved_settings.fred_api_key, resolved_settings.request_timeout_seconds)
    app.extensions["market_regime"] = market_regime or MarketRegimeService(app.extensions["fred"], app.extensions["market_data"], resolved_settings.regime_snapshot_root)
    app.extensions["score_history"] = ScoreHistoryService(resolved_settings.score_history_db_path)
    app.extensions["event_intelligence"] = EventIntelligenceService(app.extensions["news"],app.extensions["sentiment"],app.extensions["sec_edgar"],app.extensions["market_data"],app.extensions["score_history"],app.extensions["paper_execution"])
    app.extensions["news_intelligence"] = NewsIntelligenceService(app.extensions["news"],app.extensions["sentiment"],resolved_settings.news_intelligence_db_path)
    app.register_blueprint(system_blueprint, url_prefix="/api")
    app.register_blueprint(market_blueprint, url_prefix="/api")
    app.register_blueprint(news_blueprint, url_prefix="/api")
    app.register_blueprint(sentiment_blueprint, url_prefix="/api")
    app.register_blueprint(scoring_blueprint, url_prefix="/api")
    app.register_blueprint(model_lab_blueprint, url_prefix="/api")
    app.register_blueprint(fundamentals_blueprint, url_prefix="/api")
    app.register_blueprint(paper_blueprint, url_prefix="/api")
    app.register_blueprint(risk_blueprint, url_prefix="/api")
    app.register_blueprint(regime_blueprint, url_prefix="/api")
    app.register_blueprint(events_blueprint, url_prefix="/api")
    app.register_blueprint(news_intelligence_blueprint, url_prefix="/api")

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
