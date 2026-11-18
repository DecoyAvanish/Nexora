"""Institutional-style analytics for fill-derived paper portfolios."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


class PortfolioRiskService:
    def __init__(self, execution, market_data, universe_path="data/sp500_universe.csv"):
        self.execution, self.market_data, self.universe_path = execution, market_data, Path(universe_path)

    def analyze(self, user_id, simulations=5000, horizon_days=63):
        account = self.execution.account(user_id); positions = account["positions"]
        if not positions: return {"status":"empty","message":"Place a paper trade to unlock portfolio risk analytics.","paper_only":True}
        symbols=[p["symbol"] for p in positions]; values=np.array([p["market_value"] for p in positions],dtype=float); weights=values/values.sum()
        returns=self._returns(symbols+["SPY"]); asset_returns=returns[symbols].dropna(); aligned=asset_returns.join(returns["SPY"],how="inner").dropna()
        portfolio=aligned[symbols].dot(weights); spy=aligned["SPY"]
        downside=portfolio[portfolio<0]; annual_return=portfolio.mean()*252; annual_vol=portfolio.std(ddof=1)*np.sqrt(252)
        beta=np.cov(portfolio,spy,ddof=1)[0,1]/np.var(spy,ddof=1) if np.var(spy,ddof=1)>0 else 0
        sharpe=annual_return/annual_vol if annual_vol else 0; downside_vol=downside.std(ddof=1)*np.sqrt(252) if len(downside)>1 else 0
        cumulative=(1+portfolio).cumprod(); drawdown=cumulative/cumulative.cummax()-1; var=float(np.quantile(portfolio,.05)); es=float(portfolio[portfolio<=var].mean())
        correlation=asset_returns.corr(); covariance=asset_returns.cov().to_numpy()*252; contribution=weights*(covariance@weights); contribution=contribution/contribution.sum() if contribution.sum() else contribution
        sectors=self._sectors(); sector_exposure={}
        for symbol,weight in zip(symbols,weights): sector_exposure[sectors.get(symbol,"Other")]=sector_exposure.get(sectors.get(symbol,"Other"),0)+float(weight)
        hhi=float(np.sum(weights**2)); effective=1/hhi if hhi else 0; diversification=max(0,min(100,(effective/max(len(weights),1))*100*(1-float(correlation.where(~np.eye(len(symbols),dtype=bool)).stack().mean() if len(symbols)>1 else 0))))
        factor_exposure=self._factor_exposure(portfolio, returns)
        stress=self._stress(symbols,weights,sectors,beta)
        rng=np.random.default_rng(42); simulated=rng.multivariate_normal(asset_returns.mean().to_numpy(),asset_returns.cov().to_numpy(),size=(min(max(simulations,100),20000),horizon_days)); terminal=np.prod(1+simulated@weights,axis=1)-1
        warnings=[]
        for sector,weight in sector_exposure.items():
            if weight>.4: warnings.append({"severity":"high","type":"concentration","title":"HIGH CONCENTRATION RISK","message":f"{weight:.0%} of portfolio value is exposed to {sector}."})
        top=int(np.argmax(contribution));
        if contribution[top]>.5: warnings.append({"severity":"high","type":"variance","title":"CORRELATION WARNING","message":f"{symbols[top]} contributes {contribution[top]:.0%} of estimated portfolio variance."})
        return {"status":"ready","as_of":aligned.index[-1].strftime("%Y-%m-%d"),"paper_only":True,"metrics":{"beta_vs_spy":round(float(beta),4),"annualized_volatility":round(float(annual_vol),4),"sharpe":round(float(sharpe),4),"sortino":round(float(annual_return/downside_vol if downside_vol else 0),4),"var_95_daily":round(var,4),"expected_shortfall_95":round(es,4),"maximum_drawdown":round(float(drawdown.min()),4),"concentration_hhi":round(hhi,4),"diversification_score":round(diversification,1)},"sector_exposure":sector_exposure,"correlation":{"symbols":symbols,"matrix":correlation.fillna(0).round(3).values.tolist()},"variance_contribution":dict(zip(symbols,np.round(contribution,4))),"factor_exposure":factor_exposure,"stress_tests":stress,"monte_carlo":{"simulations":len(terminal),"horizon_days":horizon_days,"median_return":round(float(np.median(terminal)),4),"p05_return":round(float(np.quantile(terminal,.05)),4),"p95_return":round(float(np.quantile(terminal,.95)),4),"probability_of_loss":round(float((terminal<0).mean()),4)},"warnings":warnings}

    def _returns(self,symbols):
        series={}
        for symbol in dict.fromkeys(symbols):
            history=self.market_data.history(symbol,"1y"); series[symbol]=pd.Series(history.closes,index=pd.to_datetime(history.dates)).pct_change()
        return pd.DataFrame(series).dropna(how="all")
    def _sectors(self):
        if not self.universe_path.exists(): return {}
        frame=pd.read_csv(self.universe_path); symbol=next((c for c in frame if c.lower() in {"symbol","ticker"}),None); sector=next((c for c in frame if "sector" in c.lower()),None)
        return dict(zip(frame[symbol].astype(str),frame[sector].fillna("Other"))) if symbol and sector else {}
    def _factor_exposure(self,portfolio,returns):
        result={"market":round(float(np.cov(portfolio,returns["SPY"].reindex(portfolio.index).fillna(0))[0,1]/np.var(returns["SPY"].reindex(portfolio.index).fillna(0))),3)}
        return result
    @staticmethod
    def _stress(symbols,weights,sectors,beta):
        tech=sum(w for s,w in zip(symbols,weights) if sectors.get(s)=="Information Technology")
        oil=sum(w for s,w in zip(symbols,weights) if sectors.get(s)=="Energy")
        return [{"scenario":"S&P 500 falls 10%","estimated_return":round(float(-.10*beta),4)},{"scenario":"Technology falls 20%","estimated_return":round(float(-.20*tech),4)},{"scenario":"Rates increase 100 bps","estimated_return":round(float(-.04*sum(weights)),4)},{"scenario":"Volatility doubles","estimated_return":round(float(-.08*sum(weights)),4)},{"scenario":"Oil increases 30%","estimated_return":round(float(.12*oil-.03*(1-oil)),4)},{"scenario":"2008-style correlation shock","estimated_return":round(float(-.25*(.5+.5*sum(weights**2))),4)}]
