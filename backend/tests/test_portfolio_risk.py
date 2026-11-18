import numpy as np

from backend.services.market_data import MarketHistory
from backend.services.portfolio_risk import PortfolioRiskService


class Execution:
    def account(self, _user):
        return {"positions":[{"symbol":"AAPL","market_value":600},{"symbol":"MSFT","market_value":400}]}


class Market:
    def history(self, symbol, _period):
        rng=np.random.default_rng(sum(map(ord,symbol))); closes=100*np.cumprod(1+rng.normal(.0005,.012,260))
        dates=np.arange("2025-11-01","2026-11-18",dtype="datetime64[D]")[:260].astype(str).tolist()
        values=closes.tolist(); return MarketHistory(symbol,dates,values,values,values,values,[1000]*260)


def test_risk_engine_returns_metrics_stress_and_monte_carlo(tmp_path):
    result=PortfolioRiskService(Execution(),Market(),tmp_path/"missing.csv").analyze("user",simulations=100,horizon_days=10)
    assert result["status"]=="ready"
    assert "beta_vs_spy" in result["metrics"]
    assert len(result["stress_tests"])==6
    assert result["monte_carlo"]["simulations"]==100
    assert result["correlation"]["symbols"]==["AAPL","MSFT"]
