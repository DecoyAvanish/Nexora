"""Active watchlist monitor for model, news, filing, market, and regime changes."""
import numpy as np
from datetime import datetime,timezone
from backend.services.market_data import normalize_symbol

class WatchlistIntelligenceService:
    def __init__(self,cross,score_history,news,events,market,regime):self.cross,self.history,self.news,self.events,self.market,self.regime=cross,score_history,news,events,market,regime
    def monitor(self,symbols,company_names=None):
        alerts=[]; company_names=company_names or {}; current_regime=self.regime.classify(persist=False)
        for raw in symbols[:50]:
            symbol=normalize_symbol(raw); snapshots=self.history.history(symbol); score=self.cross.get_score(symbol) if self.cross.available else None
            if score and snapshots:
                previous=snapshots[-1]["score"]
                if abs(score["ai_score"]-previous)>=1:alerts.append(self._alert(symbol,"score_change","high",f"{symbol} moved from {previous:g} → {score['ai_score']}","Model score changed materially since the previous observation."))
            news=self.news.analyze(symbol,company_names.get(symbol),days=7)
            if news["label"] in {"positive","negative"} and news["confidence"]["level"]!="low":alerts.append(self._alert(symbol,"sentiment_reversal","medium",f"{symbol} news sentiment is {news['label']}",f"{news['primary_theme']} · {news['source_agreement']:.0%} source agreement."))
            timeline=self.events.timeline(symbol,company_names.get(symbol),days=14)
            for event in timeline["events"]:
                if event["type"] in {"sec_8k","earnings_report","management_change","merger_acquisition","insider_transaction"}:alerts.append(self._alert(symbol,"filing_alert","medium",event["title"],event["source_url"] or "New corporate filing or event."));break
            history=self.market.history(symbol,"1y"); closes=np.asarray(history.closes); volumes=np.asarray(history.volumes); returns=np.diff(closes)/closes[:-1]; price_z=(returns[-1]-returns[-63:].mean())/(returns[-63:].std() or 1); volume_z=(volumes[-1]-volumes[-63:].mean())/(volumes[-63:].std() or 1)
            if abs(price_z)>=2 or volume_z>=2:alerts.append(self._alert(symbol,"price_volume_anomaly","high",f"Unusual activity in {symbol}",f"Price z-score {price_z:.1f}; volume z-score {volume_z:.1f}."))
            if closes[-1]>=max(closes[-252:])*.995:alerts.append(self._alert(symbol,"technical_breakout","medium",f"{symbol} is testing a 52-week high","Price is within 0.5% of its trailing high."))
            try:
                import yfinance as yf
                calendar=yf.Ticker(symbol).calendar; earnings=calendar.get("Earnings Date") if isinstance(calendar,dict) else None; earnings=earnings[0] if isinstance(earnings,list) else earnings
                if earnings:
                    when=earnings.to_pydatetime() if hasattr(earnings,"to_pydatetime") else earnings; when=when.replace(tzinfo=timezone.utc) if when.tzinfo is None else when
                    days=(when-datetime.now(timezone.utc)).days
                    if 0<=days<=14:alerts.append(self._alert(symbol,"earnings_reminder","medium",f"{symbol} earnings in {days} days",when.date().isoformat()))
            except Exception:pass
            if snapshots and snapshots[-1].get("regime") and snapshots[-1]["regime"]!=current_regime["state"]:alerts.append(self._alert(symbol,"risk_state_change","high","Market risk state changed",f"{snapshots[-1]['regime'].replace('_',' ')} → {current_regime['label']}."))
        order={"high":0,"medium":1,"low":2};alerts.sort(key=lambda item:order[item["severity"]]);return {"symbols":symbols,"regime":current_regime,"alerts":alerts,"alert_count":len(alerts)}
    @staticmethod
    def _alert(symbol,kind,severity,title,reason):return {"symbol":symbol,"type":kind,"severity":severity,"title":title,"reason":reason}
