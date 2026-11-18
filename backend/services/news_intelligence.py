"""Evidence-weighted financial news intelligence beyond average sentiment."""

from __future__ import annotations

import hashlib
import math
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from backend.services.event_intelligence import NEWS_RULES
from backend.services.market_data import normalize_symbol

CREDIBILITY={"reuters.com":1.0,"apnews.com":.98,"bloomberg.com":.95,"wsj.com":.94,"ft.com":.94,"cnbc.com":.84,"finance.yahoo.com":.78,"marketwatch.com":.76,"seekingalpha.com":.62}
POLARITY={"positive":1.0,"neutral":0.0,"negative":-1.0}


class NewsIntelligenceService:
    def __init__(self,news,sentiment,db_path="data/news_intelligence.db"):
        self.news,self.sentiment,self.path=news,sentiment,Path(db_path); self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as db: db.executescript("CREATE TABLE IF NOT EXISTS stories(symbol TEXT NOT NULL,fingerprint TEXT NOT NULL,first_seen TEXT NOT NULL,last_seen TEXT NOT NULL,topic TEXT,title TEXT,PRIMARY KEY(symbol,fingerprint)); CREATE TABLE IF NOT EXISTS volume_history(symbol TEXT NOT NULL,day TEXT NOT NULL,count INTEGER NOT NULL,PRIMARY KEY(symbol,day));")
    def _connect(self): db=sqlite3.connect(self.path); db.row_factory=sqlite3.Row; return db

    def analyze(self,raw_symbol,company=None,days=14,limit=75):
        symbol=normalize_symbol(raw_symbol); articles=self.news.company_news(symbol,company,days=max(1,min(days,90)),limit=limit); unique,duplicates=self._deduplicate(articles)
        sentiment=self.sentiment.analyze(unique); analyzed=sentiment["articles"]; now=datetime.now(timezone.utc); company_terms=self._entity_terms(symbol,company)
        evidence=[]; topics=Counter(); novel=0
        with self._connect() as db:
            known={row["fingerprint"] for row in db.execute("SELECT fingerprint FROM stories WHERE symbol=?",(symbol,))}
            for article in analyzed:
                fingerprint=self._fingerprint(article["title"]); title=article["title"].lower(); event_types=[kind for kind,terms in NEWS_RULES.items() if any(term in title for term in terms)]; topic=event_types[0] if event_types else self._topic(title)
                credibility=self._credibility(article); recency=self._recency(article.get("published_at"),now); relevance=self._relevance(title,company_terms); weight=credibility*recency*relevance; is_novel=fingerprint not in known
                if is_novel:novel+=1
                topics[topic]+=weight
                db.execute("INSERT INTO stories VALUES(?,?,?,?,?,?) ON CONFLICT(symbol,fingerprint) DO UPDATE SET last_seen=excluded.last_seen",(symbol,fingerprint,now.isoformat(),now.isoformat(),topic,article["title"]))
                evidence.append({**article,"fingerprint":fingerprint,"credibility_weight":round(credibility,3),"recency_weight":round(recency,3),"entity_relevance":round(relevance,3),"evidence_weight":round(weight,3),"event_types":event_types,"topic":topic,"novel":is_novel})
            day=now.date().isoformat(); db.execute("INSERT INTO volume_history VALUES(?,?,?) ON CONFLICT(symbol,day) DO UPDATE SET count=excluded.count",(symbol,day,len(unique)))
            history=[row[0] for row in db.execute("SELECT count FROM volume_history WHERE symbol=? AND day<? ORDER BY day DESC LIMIT 30",(symbol,day))]
        weighted=sum(POLARITY.get(item["sentiment"],0)*item["sentiment_confidence"]*item["evidence_weight"] for item in evidence); total=sum(item["evidence_weight"] for item in evidence); score=weighted/total if total else 0
        positive=sum(item["evidence_weight"] for item in evidence if item["sentiment"]=="positive"); negative=sum(item["evidence_weight"] for item in evidence if item["sentiment"]=="negative"); agreement=max(positive,negative,sum(item["evidence_weight"] for item in evidence if item["sentiment"]=="neutral"))/total if total else 0
        contradictions=self._contradictions(evidence); unusual=self._unusual(len(unique),history); confidence=self._confidence(len(evidence),agreement,total)
        return {"symbol":symbol,"sentiment_score":round(score,4),"label":"positive" if score>=.15 else "negative" if score<=-.15 else "neutral","confidence":confidence,"coverage":len(evidence),"raw_article_count":len(articles),"duplicate_count":duplicates,"novel_events":novel,"source_agreement":round(agreement,4),"sentiment_disagreement":round(1-agreement,4),"primary_theme":self._label(topics.most_common(1)[0][0]) if topics else "Insufficient coverage","topic_clusters":[{"topic":self._label(topic),"weight":round(weight,3)} for topic,weight in topics.most_common(5)],"contradictions":contradictions,"unusual_news_volume":unusual,"articles":sorted(evidence,key=lambda item:item["evidence_weight"],reverse=True),"methodology":{"recency_half_life_hours":72,"deduplication":"normalized-title fingerprint","credibility":"domain reliability tiers","novelty":"first-seen story fingerprint"}}

    def _deduplicate(self,articles):
        best={}
        for article in articles:
            key=self._fingerprint(article.title); current=best.get(key)
            if not current or self._credibility(article.to_dict())>self._credibility(current.to_dict()):best[key]=article
        return list(best.values()),len(articles)-len(best)
    @staticmethod
    def _fingerprint(title):
        normalized=re.sub(r"\b(reuters|exclusive|update\s*\d*|breaking)\b","",title.lower()); normalized=re.sub(r"[^a-z0-9 ]"," ",normalized); stop={"after","amid","says","the","and","for","with","from"}; tokens=sorted(set(token for token in normalized.split() if len(token)>2 and token not in stop))
        return hashlib.sha256(" ".join(tokens).encode()).hexdigest()[:24]
    @staticmethod
    def _entity_terms(symbol,company): return {symbol.lower(),*[token.lower().strip(".,") for token in (company or "").split() if len(token)>3]}
    @staticmethod
    def _relevance(title,terms): return min(1,.45+.2*sum(term in title for term in terms))
    @staticmethod
    def _recency(published,now):
        if not published:return .5
        age=max(0,(now-datetime.fromisoformat(published.replace("Z","+00:00"))).total_seconds()/3600); return math.exp(-math.log(2)*age/72)
    @staticmethod
    def _credibility(article):
        domain=(article.get("domain") or urlparse(article.get("url","")).hostname or "").lower().removeprefix("www.")
        return next((weight for known,weight in CREDIBILITY.items() if domain.endswith(known)),.58)
    @staticmethod
    def _topic(title):
        terms={"artificial_intelligence":(" ai ","artificial intelligence"),"financial_performance":("revenue","profit","margin"),"market_activity":("shares","stock","market"),"operations":("factory","supply","production")}
        return next((topic for topic,words in terms.items() if any(word in f" {title} " for word in words)),"company_update")
    @staticmethod
    def _contradictions(evidence):
        result=[]
        for topic in {item["topic"] for item in evidence}:
            items=[item for item in evidence if item["topic"]==topic]; labels={item["sentiment"] for item in items}
            if {"positive","negative"}.issubset(labels):result.append({"topic":NewsIntelligenceService._label(topic),"articles":len(items),"description":"Credible sources express opposing directional interpretations."})
        return result
    @staticmethod
    def _unusual(current,history):
        if len(history)<5:return {"detected":False,"ratio_to_baseline":None,"baseline_days":len(history)}
        mean=sum(history)/len(history); variance=sum((value-mean)**2 for value in history)/len(history); z=(current-mean)/(variance**.5 or 1)
        return {"detected":z>=2,"z_score":round(z,2),"ratio_to_baseline":round(current/mean,2) if mean else None,"baseline_days":len(history)}
    @staticmethod
    def _confidence(count,agreement,total):
        value=min(1,count/12)*.4+agreement*.4+min(1,total/8)*.2
        return {"level":"high" if value>=.75 else "medium" if value>=.45 else "low","score":round(value,3)}
    @staticmethod
    def _label(value):return value.replace("_"," ").title()
