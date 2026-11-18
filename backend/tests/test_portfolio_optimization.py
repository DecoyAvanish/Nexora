import numpy as np
from backend.services.market_data import MarketHistory
from backend.services.portfolio_optimization import PortfolioOptimizationService

class Market:
    def history(self,symbol,period):
        rng=np.random.default_rng(sum(map(ord,symbol))); prices=100*np.cumprod(1+rng.normal(.0005,.01,260));dates=np.arange("2025-01-01","2026-01-01",dtype="datetime64[D]")[:260].astype(str).tolist();values=prices.tolist();return MarketHistory(symbol,dates,values,values,values,values,[1000]*260)
class Cross:
    def get_score(self,symbol):return {"ai_score":{"AAA":9,"BBB":7,"CCC":5}[symbol]}

def test_optimizer_returns_allocation_and_efficient_frontier(tmp_path):
    service=PortfolioOptimizationService(Market(),Cross(),tmp_path/"missing.csv")
    result=service.optimize(["AAA","BBB","CCC"],"maximum_sharpe",1,500)
    assert abs(sum(item["weight"] for item in result["allocation"])-1)<1e-5
    assert result["efficient_frontier"]
    assert "not guaranteed" in result["disclaimer"]

def test_ai_weighting_favors_higher_score(tmp_path):
    result=PortfolioOptimizationService(Market(),Cross(),tmp_path/"missing.csv").optimize(["AAA","BBB","CCC"],"ai_score_weighted",1,500)
    assert result["allocation"][0]["weight"]>result["allocation"][-1]["weight"]
