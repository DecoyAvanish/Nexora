"""Transparent long-only portfolio optimization with efficient-frontier sampling."""
import numpy as np
import pandas as pd
from backend.errors import ApiError

class PortfolioOptimizationService:
    def __init__(self,market_data,cross_sectional,universe_path="data/sp500_universe.csv"):
        self.market,self.cross,self.universe_path=market_data,cross_sectional,universe_path
    def optimize(self,symbols,mode="equal_weight",sector_limit=.4,simulations=4000):
        symbols=list(dict.fromkeys(str(symbol).upper() for symbol in symbols))
        if not 2<=len(symbols)<=30:raise ApiError("Choose between 2 and 30 symbols.",400,"invalid_portfolio_size")
        series={}
        for symbol in symbols:
            history=self.market.history(symbol,"1y");series[symbol]=pd.Series(history.closes,index=pd.to_datetime(history.dates)).pct_change()
        frame=pd.DataFrame(series).dropna(); mean=frame.mean().to_numpy()*252; covariance=frame.cov().to_numpy()*252; rng=np.random.default_rng(42); count=min(max(int(simulations),500),20000); candidates=rng.dirichlet(np.ones(len(symbols)),count)
        sectors=self._sectors(); valid=np.array([all(sum(weight for weight,symbol in zip(row,symbols) if sectors.get(symbol,"Other")==sector)<=sector_limit+1e-9 for sector in set(sectors.get(symbol,"Other") for symbol in symbols)) for row in candidates]); candidates=candidates[valid]
        if not len(candidates):raise ApiError("Sector constraints leave no feasible allocation.",422,"infeasible_constraints")
        returns=candidates@mean; volatility=np.sqrt(np.einsum("ij,jk,ik->i",candidates,covariance,candidates)); sharpe=np.divide(returns,volatility,out=np.zeros_like(returns),where=volatility>0)
        if mode=="equal_weight":weights=np.ones(len(symbols))/len(symbols)
        elif mode=="minimum_variance":weights=candidates[np.argmin(volatility)]
        elif mode=="maximum_sharpe":weights=candidates[np.argmax(sharpe)]
        elif mode=="risk_parity":weights=self._risk_parity(covariance)
        elif mode=="ai_score_weighted":
            scores=np.array([self.cross.get_score(symbol)["ai_score"] for symbol in symbols],dtype=float);weights=scores/scores.sum()
        elif mode=="sector_constrained":weights=candidates[np.argmax(sharpe)]
        else:raise ApiError("Unknown optimization mode.",400,"invalid_optimization_mode")
        expected=float(weights@mean); risk=float(np.sqrt(weights@covariance@weights)); frontier_idx=np.linspace(0,len(candidates)-1,min(80,len(candidates))).astype(int); ordered=np.argsort(volatility)
        return {"mode":mode,"allocation":[{"symbol":symbol,"weight":round(float(weight),6),"sector":sectors.get(symbol,"Other")} for symbol,weight in zip(symbols,weights)],"expected_annual_return":expected,"annualized_volatility":risk,"historical_sharpe":expected/risk if risk else 0,"efficient_frontier":[{"volatility":float(volatility[ordered[index]]),"return":float(returns[ordered[index]])} for index in frontier_idx],"disclaimer":"Optimized historical allocations are not guaranteed forecasts. Expected returns and covariances can change abruptly."}
    @staticmethod
    def _risk_parity(covariance):
        weights=np.ones(len(covariance))/len(covariance)
        for _ in range(500):
            marginal=covariance@weights; contribution=weights*marginal; target=(weights@covariance@weights)/len(weights); weights*=np.sqrt(np.divide(target,contribution,out=np.ones_like(contribution),where=contribution>0));weights=np.maximum(weights,1e-6);weights/=weights.sum()
        return weights
    def _sectors(self):
        try:
            frame=pd.read_csv(self.universe_path); symbol=next(column for column in frame if column.lower() in {"ticker","symbol"}); sector=next(column for column in frame if "sector" in column.lower());return dict(zip(frame[symbol],frame[sector]))
        except Exception:return {}
