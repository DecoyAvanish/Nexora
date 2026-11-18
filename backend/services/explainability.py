"""First-class, evidence-linked model explanation assembly."""

from __future__ import annotations

from backend.errors import ApiError
from backend.services.market_data import normalize_symbol


class ExplainabilityService:
    def __init__(self,cross_sectional,fundamentals,news_intelligence,market_data,score_history):
        self.cross,self.fundamentals,self.news,self.market,self.history=cross_sectional,fundamentals,news_intelligence,market_data,score_history

    def explain(self,raw_symbol,company=None):
        symbol=normalize_symbol(raw_symbol); warnings=[]
        if not self.cross.available:raise ApiError("Publish the production model before requesting full explanations.",503,"model_not_published")
        score=self.cross.get_score(symbol); shap=self.cross.explain(symbol)
        try: fundamentals=self.fundamentals.analyze(symbol)
        except ApiError as error: fundamentals={"metrics":{},"drivers":{"positive":[],"negative":[]},"status":"unavailable"}; warnings.append(f"Fundamental data unavailable: {error.code}")
        try: news=self.news.analyze(symbol,company)
        except ApiError as error: news={"status":"unavailable","coverage":0,"confidence":{"level":"low","score":0},"articles":[],"label":"unavailable"}; warnings.append(f"News intelligence unavailable: {error.code}")
        history=self.market.history(symbol,"1y"); snapshots=self.history.history(symbol)
        categories={"technical":0.0,"fundamental":0.0,"sentiment":0.0}
        for item in shap["waterfall"]:categories[item["category"]]+=item["value"]
        absolute=sum(abs(value) for value in categories.values())
        contributions={key:{"raw":round(value,5),"share_of_absolute_impact":round(abs(value)/absolute,4) if absolute else 0,"included_in_model":any(item["category"]==key for item in shap["waterfall"])} for key,value in categories.items()}
        for category in ("fundamental","sentiment"):
            if not contributions[category]["included_in_model"]:warnings.append(f"{category.title()} evidence is displayed for context but is not present in this production model artifact.")
        if news.get("coverage",0)<5:warnings.append("Signal confidence is limited by sparse news coverage.")
        unavailable=[name for name,metric in fundamentals.get("metrics",{}).items() if metric.get("status")!="available"]
        if unavailable:warnings.append(f"Missing fundamental inputs: {', '.join(unavailable[:6])}.")
        sources=[]
        for article in news.get("articles",[])[:8]:sources.append({"type":"news","label":article["title"],"url":article["url"],"published_at":article.get("published_at")})
        for metric in fundamentals.get("metrics",{}).values():
            for source in metric.get("sources",[]):
                if source.get("document_url") and not any(item["url"]==source["document_url"] for item in sources):sources.append({"type":"sec","label":f"{source.get('form')} · {source.get('concept')}","url":source["document_url"],"published_at":source.get("accepted_at")})
        positives=shap["top_positive"]; negatives=shap["top_negative"]
        insights=[]
        if score.get("universe_percentile") is not None:insights.append(f"The model score ranks above {score['universe_percentile']:.0f}% of the current universe; similar feature combinations were historically associated with outperformance in training data.")
        if score.get("sector_percentile") is not None:insights.append(f"Within {score.get('sector') or 'its sector'}, the stock ranks at the {score['sector_percentile']:.0f}th percentile.")
        return {"symbol":symbol,"score":score,"summary":{"language":"historical_association","insights":insights,"news":{key:news.get(key) for key in ("label","confidence","coverage","novel_events","source_agreement","primary_theme","unusual_news_volume")}},"drivers":{"positive":positives,"negative":negatives,"fundamental_context":fundamentals.get("drivers",{})},"contributions":contributions,"shap":{"baseline":shap["baseline"],"waterfall":shap["waterfall"][:12],"units":"raw model margin; directional, not probability points"},"sector_comparison":{"sector":score.get("sector"),"universe_percentile":score.get("universe_percentile"),"sector_percentile":score.get("sector_percentile"),"relative_features":[item for item in shap["waterfall"] if item["scope"]=="sector_relative"][:6]},"score_history":snapshots[-30:],"data_freshness":{"market_data_through":history.dates[-1],"model_data_through":score.get("data_through"),"model_version":score.get("model_version"),"fundamentals_as_of":fundamentals.get("as_of"),"latest_news":max((article.get("published_at") or "" for article in news.get("articles",[])),default=None)},"missing_data_warnings":warnings,"sources":sources[:16],"model_limitations":["Scores rank stocks relative to the current universe; they are not price forecasts.","SHAP values explain this model output but do not establish causality.","Historically associated patterns may fail under new regimes.","News classification can miss context, satire, or facts absent from headlines.","This research interface is not financial advice."]}
