"""Point-in-time score replay and leakage-guarded strategy backtesting."""
from __future__ import annotations
import json, operator
from pathlib import Path
import numpy as np
import pandas as pd
from backend.errors import ApiError
from backend.services.market_data import normalize_symbol

OPS={">=":operator.ge,"<=":operator.le,">":operator.gt,"<":operator.lt,"==":operator.eq}
ALIASES={"ai_score":"ai_score","sentiment_score":"sentiment_probability","revenue_growth":"revenue_growth","debt_to_equity":"debt_to_equity","outperformance_probability":"probability"}

class HistoricalResearchService:
    def __init__(self,artifact_root="artifacts/cross_sectional",feature_path="data/features/cross_sectional.parquet"):
        self.root,self.feature_path=Path(artifact_root),Path(feature_path); self._scores=None; self._features=None
    def scores(self):
        if self._scores is None:
            manifest_path=self.root/"latest.json"
            if not manifest_path.exists():raise ApiError("No historical model artifact is available.",503,"history_unavailable")
            manifest=json.loads(manifest_path.read_text()); version=self.root/manifest["model_version"]
            path=version/"walk_forward_scores.csv"
            if not path.exists():raise ApiError("Walk-forward score history is not installed on this deployment.",503,"history_unavailable")
            frame=pd.read_csv(path); frame["date"]=pd.to_datetime(frame["date"],utc=True); frame["ticker"]=frame["ticker"].str.upper()
            if self.feature_path.exists():
                features=pd.read_parquet(self.feature_path); features["date"]=pd.to_datetime(features["date"],utc=True); features["ticker"]=features["ticker"].str.upper(); extra=[column for column in features.columns if column not in frame.columns and column not in {"fwd_ret_63d","bench_ret_63d","y"}]
                frame=frame.merge(features[["date","ticker",*extra]],on=["date","ticker"],how="left")
            self._scores=frame
        return self._scores
    def replay(self,symbol,as_of):
        ticker=normalize_symbol(symbol); target=pd.Timestamp(as_of,tz="UTC") if pd.Timestamp(as_of).tzinfo is None else pd.Timestamp(as_of).tz_convert("UTC"); frame=self.scores(); rows=frame[(frame.ticker==ticker)&(frame.date<=target)].sort_values("date")
        if rows.empty:raise ApiError(f"No point-in-time score exists for {ticker} on or before {as_of}.",404,"replay_not_found")
        row=rows.iloc[-1]; available={key:self._clean(row[key]) for key in ("probability","momentum_probability","technical_probability","sentiment_probability","ai_score","universe_percentile","sector_percentile","sector") if key in row and pd.notna(row[key])}
        drivers=[]
        for key in ("probability","momentum_probability","technical_probability","sentiment_probability"):
            if key in available:drivers.append({"feature":key,"direction":"positive" if available[key]>=.5 else "negative","strength":round(abs(available[key]-.5),4),"value":available[key]})
        drivers.sort(key=lambda item:item["strength"],reverse=True); forward=self._clean(row.get("fwd_ret_63d")); benchmark=self._clean(row.get("bench_ret_63d")); outcome=None if forward is None or benchmark is None else forward>benchmark
        return {"symbol":ticker,"requested_date":str(as_of)[:10],"score_date":row.date.date().isoformat(),"score":int(row.ai_score),"outperformance_probability":self._clean(row.get("probability")),"information_available_then":available,"primary_drivers":drivers[:5],"subsequent_63_trading_day_return":forward,"benchmark_63_trading_day_return":benchmark,"subsequent_excess_return":None if forward is None or benchmark is None else round(forward-benchmark,6),"signal_correct":outcome,"integrity":{"point_in_time":True,"forward_return_used_for_scoring":False,"note":"Outcome fields are joined only after replaying the contemporaneous score."}}
    def backtest(self,config):
        frame=self.scores().copy(); conditions=config.get("conditions",[])
        for condition in conditions:
            field=ALIASES.get(condition.get("field")); op=OPS.get(condition.get("operator"));
            if not field or field not in frame.columns:raise ApiError(f"Point-in-time field '{condition.get('field')}' is unavailable; the backtest was stopped to prevent substitution leakage.",422,"pit_feature_unavailable")
            threshold=float(condition["value"]); comparable=frame[field]*100 if condition.get("field")=="sentiment_score" else frame[field]; frame=frame[op(comparable,threshold)]
        schedule=config.get("rebalance","monthly"); period={"weekly":"W-FRI","monthly":"M","quarterly":"Q"}.get(schedule)
        if not period:raise ApiError("Rebalance must be weekly, monthly, or quarterly.",400,"invalid_rebalance")
        frame["rebalance_date"]=frame["date"].dt.to_period(period).dt.end_time.dt.tz_localize("UTC"); chosen=[]
        maximum=max(1,min(int(config.get("max_positions",20)),100)); sector_limit=float(config.get("sector_limit",1)); weighting=config.get("weighting","equal")
        for _,group in frame.sort_values(["date","probability"]).groupby("rebalance_date"):
            snapshot=group[group.date==group.date.max()].sort_values("probability",ascending=False); selected=[]; sector_counts={}
            for row in snapshot.itertuples():
                if len(selected)>=maximum:break
                sector=getattr(row,"sector","Unknown"); allowed=max(1,int(np.floor(maximum*sector_limit)))
                if sector_counts.get(sector,0)>=allowed:continue
                selected.append(row);sector_counts[sector]=sector_counts.get(sector,0)+1
            if not selected:continue
            if weighting=="equal":raw=np.ones(len(selected))
            elif weighting=="score":raw=np.array([max(.001,getattr(row,"probability",.5)) for row in selected])
            elif weighting=="volatility":
                if "volatility_63d" not in frame.columns:raise ApiError("Volatility weighting requires point-in-time volatility_63d.",422,"pit_feature_unavailable")
                raw=np.array([1/max(.01,float(getattr(row,"volatility_63d"))) for row in selected])
            else:raise ApiError("Weighting must be equal, score, or volatility.",400,"invalid_weighting")
            weights=raw/raw.sum(); chosen.append((group.rebalance_date.iloc[0],selected,weights))
        cost_bps=float(config.get("transaction_cost_bps",5))+float(config.get("slippage_bps",5)); results=[];trades=[];previous={}
        scale={"weekly":5/63,"monthly":21/63,"quarterly":1}[schedule]
        for date,selected,weights in chosen:
            current={row.ticker:float(weight) for row,weight in zip(selected,weights)}; turnover=sum(abs(current.get(ticker,0)-previous.get(ticker,0)) for ticker in set(current)|set(previous))/2
            gross=sum(weight*float(row.fwd_ret_63d)*scale for row,weight in zip(selected,weights)); bench=float(np.nanmean([row.bench_ret_63d for row in selected]))*scale; net=gross-turnover*cost_bps/10000
            results.append({"date":date.date().isoformat(),"gross_return":gross,"net_return":net,"benchmark_return":bench,"turnover":turnover,"positions":len(selected)})
            for row,weight in zip(selected,weights):trades.append({"date":date.date().isoformat(),"ticker":row.ticker,"sector":getattr(row,"sector",None),"weight":float(weight),"ai_score":int(row.ai_score),"probability":float(row.probability)})
            previous=current
        returns=pd.Series([item["net_return"] for item in results],dtype=float); benchmark=pd.Series([item["benchmark_return"] for item in results],dtype=float); cumulative=(1+returns).cumprod(); drawdown=cumulative/cumulative.cummax()-1 if len(cumulative) else pd.Series(dtype=float)
        metrics={"periods":len(results),"cumulative_return":float(cumulative.iloc[-1]-1) if len(cumulative) else 0,"benchmark_return":float((1+benchmark).prod()-1) if len(benchmark) else 0,"sharpe":float(returns.mean()/returns.std()*np.sqrt({"weekly":52,"monthly":12,"quarterly":4}[schedule])) if len(returns)>1 and returns.std() else 0,"maximum_drawdown":float(drawdown.min()) if len(drawdown) else 0,"average_turnover":float(np.mean([item["turnover"] for item in results])) if results else 0}
        return {"configuration":config,"metrics":metrics,"periods":results,"trades":trades,"integrity":{"point_in_time_conditions":True,"outcomes_joined_after_selection":True,"return_method":"63-day realized returns scaled to rebalance interval; research approximation"}}
    @staticmethod
    def _clean(value):return None if value is None or (isinstance(value,float) and np.isnan(value)) else value.item() if hasattr(value,"item") else value
