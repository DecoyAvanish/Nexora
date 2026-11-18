from datetime import datetime,timezone
from backend.services.news import NewsArticle
from backend.services.news_intelligence import NewsIntelligenceService

NOW=datetime.now(timezone.utc).isoformat()
class News:
    def company_news(self,*args,**kwargs):return [NewsArticle("Apple raises guidance after strong demand","https://reuters.com/a","reuters.com",NOW,None,"English"),NewsArticle("Strong demand: Apple raises guidance","https://example.com/syndicated","example.com",NOW,None,"English"),NewsArticle("Apple guidance faces demand risks","https://ft.com/b","ft.com",NOW,None,"English")]
class Sentiment:
    def analyze(self,articles):
        output=[]
        for article in articles:output.append({**article.to_dict(),"sentiment":"negative" if "risks" in article.title else "positive","sentiment_confidence":.9})
        return {"articles":output}

def test_news_intelligence_weights_deduplicates_and_detects_contradictions(tmp_path):
    result=NewsIntelligenceService(News(),Sentiment(),tmp_path/"news.db").analyze("AAPL","Apple")
    assert result["duplicate_count"]==1
    assert result["coverage"]==2
    assert result["novel_events"]==2
    assert result["primary_theme"]=="Guidance Change"
    assert result["contradictions"]
    assert result["articles"][0]["credibility_weight"]>=.94

def test_seen_stories_are_not_novel_on_second_analysis(tmp_path):
    service=NewsIntelligenceService(News(),Sentiment(),tmp_path/"news.db"); service.analyze("AAPL","Apple")
    assert service.analyze("AAPL","Apple")["novel_events"]==0
