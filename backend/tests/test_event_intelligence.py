from datetime import datetime,timezone

from backend.services.event_intelligence import EventIntelligenceService
from backend.services.market_data import MarketHistory
from backend.services.news import NewsArticle


NOW=datetime.now(timezone.utc).isoformat()

class News:
    def company_news(self,*args,**kwargs):return [NewsArticle("Example launches a major product","https://news.example/product","Example News","2026-11-17T12:00:00+00:00",None,"English"),NewsArticle("Example cuts guidance after earnings miss","https://news.example/story","Example News",NOW,None,"English")]
class Sentiment:
    def analyze(self,articles):return {"articles":[{**articles[0].to_dict(),"sentiment":"positive","sentiment_confidence":.9},{**articles[1].to_dict(),"sentiment":"negative","sentiment_confidence":.94}]}
class Sec:
    def recent_filings(self,*args,**kwargs):return {"filings":[{"form":"8-K","accepted_at":NOW,"document_url":"https://sec.example/8k","items":"2.02,7.01","accession_number":"1"},{"form":"4","accepted_at":NOW,"document_url":"https://sec.example/4","items":"","accession_number":"2"}]}
class Market:
    def history(self,*args):return MarketHistory("TEST",["2026-11-17","2026-11-18"],[100,96],[101,97],[99,95],[100,96],[1000,2000])
class Scores:
    def history(self,*args):return [{"score":8,"recorded_at":"2026-11-17T15:00:00+00:00","regime":"risk_on_expansion"},{"score":5,"recorded_at":NOW,"regime":"high_volatility_risk_off"}]
class Paper:
    def ledger(self,user):return [{"created_at":NOW,"metadata":{"symbol":"TEST","side":"sell","quantity":"1","price":"96"}}]

def test_timeline_combines_news_filings_prices_scores_and_trades():
    result=EventIntelligenceService(News(),Sentiment(),Sec(),Market(),Scores(),Paper()).timeline("TEST",days=30,user_id="user")
    types={event["type"] for event in result["events"]}
    assert {"guidance_change","earnings_report","insider_transaction","price_move","sentiment_change","ai_score_change","trade"}.issubset(types)

def test_score_explanation_links_nearby_negative_events():
    result=EventIntelligenceService(News(),Sentiment(),Sec(),Market(),Scores(),Paper()).explain_score_change("TEST",days=30)
    assert "fell from 8 to 5" in result["explanation"]
    assert result["primary_drivers"]
