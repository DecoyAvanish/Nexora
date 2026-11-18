import json
import pandas as pd
from backend.errors import ApiError
from backend.services.historical_research import HistoricalResearchService

def service(tmp_path):
    root=tmp_path/"artifacts";version=root/"v1";version.mkdir(parents=True);(root/"latest.json").write_text(json.dumps({"model_version":"v1"}))
    rows=[]
    for date in pd.date_range("2025-01-31",periods=6,freq="ME"):
        for index,ticker in enumerate(("AAA","BBB","CCC")):rows.append({"date":date,"ticker":ticker,"sector":"Tech" if index<2 else "Health","probability":.8-index*.15,"momentum_probability":.7-index*.1,"technical_probability":.75-index*.1,"sentiment_probability":.7-index*.1,"ai_score":9-index*2,"universe_percentile":90-index*20,"sector_percentile":85-index*15,"fwd_ret_63d":.12-index*.06,"bench_ret_63d":.04,"y":index<2})
    pd.DataFrame(rows).to_csv(version/"walk_forward_scores.csv",index=False);return HistoricalResearchService(root)

def test_replay_separates_point_in_time_score_from_future_outcome(tmp_path):
    result=service(tmp_path).replay("AAA","2025-02-15")
    assert result["score_date"]=="2025-01-31" and result["score"]==9
    assert result["signal_correct"] is True
    assert result["integrity"]["forward_return_used_for_scoring"] is False

def test_strategy_filters_weights_and_reports_cost_adjusted_metrics(tmp_path):
    result=service(tmp_path).backtest({"conditions":[{"field":"ai_score","operator":">=","value":7}],"rebalance":"monthly","max_positions":2,"weighting":"score","transaction_cost_bps":5,"slippage_bps":5,"sector_limit":1})
    assert result["metrics"]["periods"]==6
    assert all(trade["ai_score"]>=7 for trade in result["trades"])
    assert result["periods"][0]["net_return"]<result["periods"][0]["gross_return"]

def test_strategy_rejects_unavailable_historical_field(tmp_path):
    try:service(tmp_path).backtest({"conditions":[{"field":"revenue_growth","operator":">=","value":10}],"rebalance":"monthly"})
    except ApiError as error:assert error.code=="pit_feature_unavailable"
    else:raise AssertionError("Unavailable point-in-time field was accepted")
