from backend.services.research_assistant import ResearchAssistantService
class Cross:
    def get_score(self,symbol):return {"ai_score":9 if symbol=="AAPL" else 7,"outperformance_probability":.7 if symbol=="AAPL" else .6,"universe_percentile":90,"sector_percentile":80,"model_version":"v1"}
def test_assistant_separates_retrieved_facts_from_synthesis():
    result=ResearchAssistantService(Cross(),None,None,None,None,None,None).answer("Why is AAPL scored higher than MSFT?")
    assert len(result["facts"])==2 and result["generated_explanation"]
    assert result["guardrails"]["retrieval_only"] is True and result["trace"][0]["retriever"]=="production_model"
