from backend.services.explainability import ExplainabilityService
from backend.services.market_data import MarketHistory

class Cross:
    available=True
    def get_score(self,symbol):return {"ai_score":9,"outperformance_probability":.67,"universe_percentile":93,"sector_percentile":88,"sector":"Technology","model_version":"v1","data_through":"2026-11-17"}
    def explain(self,symbol):
        items=[{"feature":"momentum_sector_rank","label":"Momentum Sector Rank","value":.4,"feature_value":.91,"direction":"positive","category":"technical","scope":"sector_relative"},{"feature":"volatility_universe_rank","label":"Volatility Universe Rank","value":-.2,"feature_value":.3,"direction":"negative","category":"technical","scope":"universe_relative"}]
        return {"baseline":0.1,"waterfall":items,"top_positive":[items[0]],"top_negative":[items[1]]}
class Fundamentals:
    def analyze(self,symbol):return {"as_of":"2026-11-18","metrics":{"roe":{"status":"available","sources":[{"form":"10-Q","concept":"NetIncomeLoss","document_url":"https://sec.example/q","accepted_at":"2026-11-01"}]}},"drivers":{"positive":[],"negative":[]}}
class News:
    def analyze(self,*args):return {"label":"positive","confidence":{"level":"medium","score":.6},"coverage":3,"novel_events":2,"source_agreement":.78,"primary_theme":"Raised Forward Guidance","unusual_news_volume":{"detected":False},"articles":[{"title":"Guidance raised","url":"https://news.example/a","published_at":"2026-11-18"}]}
class Market:
    def history(self,*args):return MarketHistory("AAPL",["2026-11-17"],[1],[1],[1],[1],[1])
class History:
    def history(self,*args):return [{"score":8,"recorded_at":"2026-11-17"},{"score":9,"recorded_at":"2026-11-18"}]

def test_explanation_is_evidence_linked_and_honest_about_missing_modalities():
    result=ExplainabilityService(Cross(),Fundamentals(),News(),Market(),History()).explain("AAPL")
    assert result["drivers"]["positive"][0]["feature"]=="momentum_sector_rank"
    assert result["shap"]["waterfall"][1]["direction"]=="negative"
    assert result["sector_comparison"]["sector_percentile"]==88
    assert result["summary"]["news"]["source_agreement"]==.78
    assert any("not present" in warning for warning in result["missing_data_warnings"])
    assert any(source["type"]=="sec" for source in result["sources"])
