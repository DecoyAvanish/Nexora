from backend.services.score_history import ScoreHistoryService

def test_score_snapshots_are_durable(tmp_path):
    service=ScoreHistoryService(tmp_path/"scores.db")
    service.record("AAPL",{"ai_score":8,"outperformance_probability":.67,"model_version":"v1","regime_adjustment":{"regime":{"state":"risk_on_expansion"}}})
    rows=service.history("AAPL")
    assert rows[0]["score"]==8
    assert rows[0]["regime"]=="risk_on_expansion"
