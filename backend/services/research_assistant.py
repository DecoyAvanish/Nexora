"""Retrieval-only research assistant with explicit facts, synthesis, sources, and trace."""
import re
from backend.errors import ApiError

class ResearchAssistantService:
    def __init__(self,cross,explainability,events,fundamentals,sec,historical,paper):self.cross,self.explainability,self.events,self.fundamentals,self.sec,self.historical,self.paper=cross,explainability,events,fundamentals,sec,historical,paper
    def answer(self,question,user_id=None):
        question=str(question).strip()
        if not 5<=len(question)<=500:raise ApiError("Ask a research question between 5 and 500 characters.",400,"invalid_question")
        symbols=list(dict.fromkeys(re.findall(r"\b[A-Z]{1,5}\b",question.upper())));stop={"WHY","WHAT","WHICH","SHOW","THIS","WEEK","LATEST"};symbols=[s for s in symbols if s not in stop];facts=[];sources=[];trace=[];lower=question.lower()
        if "higher than" in lower and len(symbols)>=2:
            scores=[self.cross.get_score(symbol) for symbol in symbols[:2]]
            for symbol,score in zip(symbols,scores):facts.append({"symbol":symbol,"ai_score":score["ai_score"],"probability":score["outperformance_probability"],"universe_percentile":score["universe_percentile"],"sector_percentile":score["sector_percentile"]})
            winner=symbols[0] if scores[0]["ai_score"]>=scores[1]["ai_score"] else symbols[1];explanation=f"{winner} ranks higher in the current model because its calibrated probability and cross-sectional feature ranks are stronger. This is historically associated with relative outperformance, not a guarantee.";trace.append({"retriever":"production_model","symbols":symbols[:2],"version":[s["model_version"] for s in scores]})
        elif "changed" in lower and symbols:
            result=self.events.explain_score_change(symbols[0],days=7);facts=result["primary_drivers"] or result["events"][:8];sources=self._event_sources(facts);explanation=result["explanation"];trace.append({"retriever":"event_timeline","symbol":symbols[0],"window_days":7,"records":len(result["events"])})
        elif "deteriorating fundamentals" in lower:
            if not user_id:raise ApiError("Sign in to inspect portfolio positions.",401,"unauthorized")
            positions=self.paper.account(user_id)["positions"]
            for position in positions:
                result=self.fundamentals.analyze(position["symbol"]);negative=result["drivers"]["negative"]
                if negative:facts.append({"symbol":position["symbol"],"negative_drivers":negative})
                sources.extend(self._fundamental_sources(result))
            explanation=f"{len(facts)} portfolio positions have one or more currently negative fundamental signals. Review the cited filing facts before drawing a conclusion.";trace.append({"retriever":"paper_positions_plus_sec_facts","positions":len(positions)})
        elif "10-q" in lower and symbols:
            result=self.fundamentals.analyze(symbols[0]);filings=self.sec.recent_filings(symbols[0],25)["filings"];quarterly=next((filing for filing in filings if filing["form"].startswith("10-Q")),None);facts=[{"metrics":result["metrics"],"positive":result["drivers"]["positive"],"negative":result["drivers"]["negative"]}];sources=self._fundamental_sources(result)
            if quarterly:sources.insert(0,{"label":f"{symbols[0]} latest 10-Q","url":quarterly["document_url"]})
            explanation=f"The latest available 10-Q facts for {symbols[0]} show {len(result['drivers']['positive'])} positive and {len(result['drivers']['negative'])} negative derived signals. This summarizes stored XBRL facts, not legal prose outside the retrieved filing.";trace.append({"retriever":"point_in_time_sec_facts","symbol":symbols[0],"as_of":result["as_of"]})
        elif "improving sentiment" in lower and "weak price momentum" in lower:
            frame=self.historical.scores();latest=frame[frame.date==frame.date.max()];matches=latest[(latest.sentiment_probability>.6)&(latest.momentum_probability<.5)].sort_values("sentiment_probability",ascending=False).head(20);facts=matches[["ticker","sentiment_probability","momentum_probability","ai_score"]].to_dict("records");explanation=f"Found {len(facts)} stocks where stored sentiment ranks are improving while price momentum remains below the neutral threshold.";trace.append({"retriever":"point_in_time_universe_snapshot","date":latest.date.max().date().isoformat(),"rows_scanned":len(latest)})
        else:raise ApiError("This retrieval assistant currently supports score comparisons, weekly changes, portfolio fundamentals, 10-Q summaries, and sentiment-versus-momentum screens.",422,"unsupported_research_intent")
        return {"question":question,"facts":facts,"generated_explanation":explanation,"sources":self._dedupe(sources),"trace":trace,"guardrails":{"retrieval_only":True,"recommendations_prohibited":True,"facts_separated_from_synthesis":True},"disclaimer":"Research synthesis only; not investment advice."}
    @staticmethod
    def _event_sources(events):return [{"label":event["title"],"url":event["source_url"]} for event in events if event.get("source_url")]
    @staticmethod
    def _fundamental_sources(result):
        sources=[]
        for metric in result.get("metrics",{}).values():
            for source in metric.get("sources",[]):
                if source.get("document_url"):sources.append({"label":f"{source.get('form')} · {source.get('concept')}","url":source["document_url"]})
        return sources
    @staticmethod
    def _dedupe(sources):return list({item["url"]:item for item in sources}.values())
