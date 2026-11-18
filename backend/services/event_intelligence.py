"""Normalize news, filings, prices, scores, and fills into an explainable event timeline."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from backend.errors import ApiError
from backend.services.market_data import normalize_symbol

NEWS_RULES={
 "earnings_report":("earnings","quarterly results","reports results"),"earnings_surprise":("beats estimates","misses estimates","earnings beat","earnings miss","surprise"),
 "guidance_change":("raises guidance","cuts guidance","lowers outlook","raises outlook","guidance"),"analyst_rating":("upgrade","downgrade","price target","initiates coverage"),
 "product_launch":("launches","unveils","new product","product launch"),"lawsuit_regulatory":("lawsuit","sued","investigation","antitrust","regulator","sec charges","ftc"),
 "management_change":("ceo resigns","appoints ceo","chief executive","cfo resigns","management change"),"capital_return":("dividend","buyback","share repurchase"),
 "merger_acquisition":("acquires","acquisition","merger","takeover","buyout","to acquire"),"insider_transaction":("insider buying","insider sale","insider sells"),
}
SEC_ITEMS={"1.01":"material_agreement","2.01":"merger_acquisition","2.02":"earnings_report","5.02":"management_change","7.01":"guidance_change","8.01":"material_corporate_event"}


class EventIntelligenceService:
    def __init__(self,news,sentiment,sec,market_data,score_history,paper_execution=None):
        self.news,self.sentiment,self.sec,self.market_data,self.score_history,self.paper_execution=news,sentiment,sec,market_data,score_history,paper_execution

    def timeline(self,raw_symbol,company=None,days=30,user_id=None):
        symbol=normalize_symbol(raw_symbol); days=max(1,min(int(days),365)); cutoff=datetime.now(timezone.utc)-timedelta(days=days); events=[]
        articles=self.news.company_news(symbol,company,days=days,limit=75)
        try: analyzed=self.sentiment.analyze(articles).get("articles",[])
        except ApiError: analyzed=[{**a.to_dict(),"sentiment":"neutral","sentiment_confidence":0} for a in articles]
        for article in analyzed:
            text=article["title"].lower(); matches=[kind for kind,terms in NEWS_RULES.items() if any(term in text for term in terms)]
            for kind in matches or ["company_news"]: events.append(self._event(kind,article.get("published_at"),article["title"],"news",article.get("url"),article.get("sentiment","neutral"),article.get("sentiment_confidence",0.5),{"publisher":article.get("domain")}))
        daily_sentiment={}
        polarity={"negative":-1,"neutral":0,"positive":1}
        for article in analyzed:
            day=(article.get("published_at") or datetime.now(timezone.utc).isoformat())[:10]
            daily_sentiment.setdefault(day,[]).append(polarity.get(article.get("sentiment"),0)*float(article.get("sentiment_confidence",0)))
        sentiment_points=[(day,sum(values)/len(values)) for day,values in sorted(daily_sentiment.items())]
        for previous,current in zip(sentiment_points,sentiment_points[1:]):
            delta=current[1]-previous[1]
            if abs(delta)>=.25: events.append(self._event("sentiment_change",f"{current[0]}T23:59:00+00:00",f"News sentiment shifted {delta:+.2f}","finbert",None,"positive" if delta>0 else "negative",min(1,abs(delta)),{"from":previous[1],"to":current[1],"delta":delta}))
        try:
            for filing in self.sec.recent_filings(symbol,100)["filings"]:
                timestamp=filing["accepted_at"]
                if self._dt(timestamp)<cutoff: continue
                if filing["form"].startswith("4"): events.append(self._event("insider_transaction",timestamp,"Insider ownership transaction filed on Form 4","sec",filing["document_url"],"neutral",.98,{"form":filing["form"],"items":filing.get("items","")}))
                elif filing["form"].startswith("8-K"):
                    items=[item.strip() for item in filing.get("items","").split(",") if item.strip()] or ["8-K"]
                    for item in items: events.append(self._event(SEC_ITEMS.get(item,"sec_8k"),timestamp,f"8-K current report — Item {item}","sec",filing["document_url"],"neutral",.99,{"form":filing["form"],"item":item,"accession":filing["accession_number"]}))
        except ApiError: pass
        history=self.market_data.history(symbol,"3mo")
        for index in range(1,len(history.closes)):
            change=history.closes[index]/history.closes[index-1]-1; timestamp=f"{history.dates[index]}T21:00:00+00:00"
            if abs(change)>=.02 and self._dt(timestamp)>=cutoff: events.append(self._event("price_move",timestamp,f"{symbol} moved {change:+.1%}","market",None,"positive" if change>0 else "negative",min(.99,.6+abs(change)*4),{"return":change,"close":history.closes[index],"volume":history.volumes[index]}))
        scores=self.score_history.history(symbol,cutoff.isoformat())
        for previous,current in zip(scores,scores[1:]):
            delta=current["score"]-previous["score"]
            if delta:events.append(self._event("ai_score_change",current["recorded_at"],f"AI Score changed from {previous['score']:g} to {current['score']:g}","nexora",None,"positive" if delta>0 else "negative",1,{"from":previous["score"],"to":current["score"],"delta":delta,"regime":current["regime"]}))
        if user_id and self.paper_execution:
            for entry in self.paper_execution.ledger(user_id):
                meta=entry.get("metadata",{})
                if meta.get("symbol")==symbol and self._dt(entry["created_at"])>=cutoff: events.append(self._event("trade",entry["created_at"],f"Paper {meta.get('side')} {meta.get('quantity')} {symbol} @ ${meta.get('price')}","paper_trading",None,"neutral",1,meta))
        events.sort(key=lambda item:item["timestamp"] or "",reverse=True)
        return {"symbol":symbol,"window_days":days,"events":events,"summary":self._summary(events),"score_history":scores}

    def explain_score_change(self,symbol,company=None,days=30,user_id=None):
        result=self.timeline(symbol,company,days,user_id); changes=[event for event in result["events"] if event["type"]=="ai_score_change"]
        if not changes:return {**result,"explanation":"No recorded AI-score change exists in this window yet. Score snapshots are recorded whenever a stock score is requested.","primary_drivers":[]}
        change=changes[0]; when=self._dt(change["timestamp"]); nearby=[event for event in result["events"] if event["type"]!="ai_score_change" and abs((self._dt(event["timestamp"])-when).total_seconds())<=3*86400]
        nearby.sort(key=lambda event:(event["sentiment"]=="negative",event["confidence"]),reverse=True); drivers=nearby[:5]
        direction="fell" if change["metadata"]["delta"]<0 else "rose"
        reason=", ".join(driver["title"] for driver in drivers[:3]) or "the underlying model factors changed"
        return {**result,"explanation":f"Nexora’s score {direction} from {change['metadata']['from']:g} to {change['metadata']['to']:g}. The closest high-confidence events were: {reason}.","primary_drivers":drivers}
    @staticmethod
    def _event(kind,timestamp,title,source,url,sentiment,confidence,metadata): return {"id":f"{source}:{kind}:{timestamp}:{title}"[:240],"type":kind,"timestamp":timestamp or datetime.now(timezone.utc).isoformat(),"title":title,"source":source,"source_url":url,"sentiment":sentiment,"confidence":round(float(confidence),3),"metadata":metadata}
    @staticmethod
    def _dt(value): return datetime.fromisoformat(value.replace("Z","+00:00"))
    @staticmethod
    def _summary(events):
        counts={};
        for event in events:counts[event["type"]]=counts.get(event["type"],0)+1
        return {"event_count":len(events),"by_type":counts,"negative_events":sum(e["sentiment"]=="negative" for e in events),"positive_events":sum(e["sentiment"]=="positive" for e in events)}
