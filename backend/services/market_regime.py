"""Five-state market-regime classification and stock-level score adjustment."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from backend.errors import ApiError

SERIES={"vix":"VIXCLS","yield_curve":"T10Y2Y","credit_spread":"BAMLH0A0HYM2","unemployment_claims":"ICSA","inflation":"CPIAUCSL","federal_funds_rate":"FEDFUNDS"}


class MarketRegimeService:
    def __init__(self, fred, market_data, snapshot_root="data/regimes"):
        self.fred,self.market_data,self.snapshot_root=fred,market_data,Path(snapshot_root)

    def classify(self, as_of=None, persist=True):
        vintage=(as_of or datetime.now(timezone.utc)).date().isoformat() if not isinstance(as_of,str) else as_of[:10]
        market=self._market_features(vintage); macro={}; sources=[]; unavailable=[]
        for name,series in SERIES.items():
            try:
                observations=self.fred.observations(series,vintage)
                macro[name]=self._transform(name,observations)
                if observations:sources.append(observations[-1])
            except ApiError as error: unavailable.append({"series_id":series,"reason":error.code})
        features={**market,**macro}; state,reasons,votes=self._state(features)
        confidence=min(.95,.45+.08*max(votes.values())+.03*(len(features)-4))
        result={"state":state,"label":state.replace("_"," ").title(),"confidence":round(confidence,3),"as_of":vintage,"features":features,"reasons":reasons,"sources":sources,"unavailable_series":unavailable,"point_in_time":True,"methodology":{"macro_source":"FRED/ALFRED realtime vintage","states":["risk_on_expansion","late_cycle","high_volatility_risk_off","recovery","sideways_uncertain"]}}
        if persist:self._persist(result)
        return result

    def adjust_score(self, score, stock_history, regime=None):
        regime=regime or self.classify(); spy=self.market_data.history("SPY","1y")
        stock_returns=np.diff(stock_history.closes)/np.asarray(stock_history.closes[:-1]); spy_returns=np.diff(spy.closes)/np.asarray(spy.closes[:-1]); length=min(len(stock_returns),len(spy_returns));
        beta=float(np.cov(stock_returns[-length:],spy_returns[-length:])[0,1]/np.var(spy_returns[-length:])) if length>20 and np.var(spy_returns[-length:]) else 1.0
        original=float(score.get("ai_score",5)); state=regime["state"]
        multipliers={"risk_on_expansion":.25,"late_cycle":-.3,"high_volatility_risk_off":-1.0,"recovery":.15,"sideways_uncertain":-.15}
        adjustment=multipliers[state]*max(.5,min(2.0,beta)); adjusted=max(1,min(10,original+adjustment)); rounded=int(round(adjusted))
        explanation=f"Score {'increased' if adjustment>0 else 'reduced'} from {original:.1f} to {adjusted:.1f} because the current regime is {regime['label'].lower()} and this stock has a {beta:.2f} beta."
        return {"original_score":original,"adjusted_score":round(adjusted,2),"adjustment":round(adjustment,2),"beta_vs_spy":round(beta,3),"explanation":explanation,"regime":regime,"display_score":rounded}

    def _market_features(self, as_of):
        today=datetime.now(timezone.utc).date().isoformat()
        if as_of < today and hasattr(self.market_data,"history_until"):
            spy=self.market_data.history_until("SPY",as_of); rsp=self.market_data.history_until("RSP",as_of)
        else:
            spy=self.market_data.history("SPY","1y"); rsp=self.market_data.history("RSP","1y")
        closes=np.asarray(spy.closes); rsp_closes=np.asarray(rsp.closes); n=min(len(closes),len(rsp_closes))
        return {"spy_trend":round(float(closes[-1]/closes[-min(200,len(closes)):].mean()-1),4),"spy_return_63d":round(float(closes[-1]/closes[-64]-1),4),"realized_volatility":round(float(np.std(np.diff(closes[-22:])/closes[-22:-1])*np.sqrt(252)),4),"market_breadth":round(float((rsp_closes[-1]/rsp_closes[-64]-1)-(closes[-1]/closes[-64]-1)),4)}
    @staticmethod
    def _transform(name,obs):
        if not obs:return None
        latest=obs[-1]["value"]
        if name=="inflation" and len(obs)>=13:return round((latest/obs[-13]["value"]-1)*100,3)
        if name=="unemployment_claims" and len(obs)>=53:return round((latest/obs[-53]["value"]-1)*100,3)
        return round(latest,4)
    @staticmethod
    def _state(f):
        v={name:0 for name in ("risk_on_expansion","late_cycle","high_volatility_risk_off","recovery","sideways_uncertain")}; reasons=[]
        trend=f.get("spy_trend",0); vol=f.get("vix",f.get("realized_volatility",.2)*100); curve=f.get("yield_curve"); credit=f.get("credit_spread"); claims=f.get("unemployment_claims"); inflation=f.get("inflation"); fed=f.get("federal_funds_rate"); breadth=f.get("market_breadth",0)
        if trend>0:v["risk_on_expansion"]+=2;v["recovery"]+=1
        else:v["high_volatility_risk_off"]+=2
        if vol>=28:v["high_volatility_risk_off"]+=3;reasons.append("Volatility is elevated")
        elif vol<20:v["risk_on_expansion"]+=2
        if curve is not None and curve<0:v["late_cycle"]+=2
        if credit is not None and credit>=5:v["high_volatility_risk_off"]+=2
        if inflation is not None and inflation>3:v["late_cycle"]+=1
        if fed is not None and fed>=4.5:v["late_cycle"]+=1
        if claims is not None and claims<0:v["recovery"]+=2
        if breadth>0:v["risk_on_expansion"]+=1;v["recovery"]+=1
        elif breadth<-.03:v["late_cycle"]+=1;v["high_volatility_risk_off"]+=1
        winner=max(v,key=v.get)
        if max(v.values())<4 or sorted(v.values(),reverse=True)[0]-sorted(v.values(),reverse=True)[1]<2:winner="sideways_uncertain"
        if not reasons:reasons=[f"SPY trend is {'positive' if trend>0 else 'negative'}",f"Market breadth is {'broad' if breadth>0 else 'narrow'}"]
        return winner,reasons,v
    def _persist(self,result):
        path=self.snapshot_root/f"{result['as_of']}.json"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(result,indent=2))
