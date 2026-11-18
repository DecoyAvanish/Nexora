from backend.services.research_journal import ResearchJournalService
class Scores:available=True
class ScoreProvider:
    available=True
    def get_score(self,symbol):return {"ai_score":8}
def test_journal_captures_score_and_measures_decision_quality(tmp_path):
    service=ResearchJournalService(tmp_path/"journal.db",ScoreProvider());entry=service.create("user",{"symbol":"AAPL","thesis_type":"earnings","thesis":"Margins should expand after the product cycle.","entry_price":100,"target_price":120,"invalidation_price":90,"model_stance":"agree"})
    assert entry["ai_score_created"]==8
    service.close("user",entry["id"],{"exit_price":110,"rule_followed":True,"reflection":"Catalyst arrived on schedule."})
    analytics=service.analytics("user");assert analytics["overall"]["win_rate"]==1 and analytics["overall"]["rule_adherence"]==1
