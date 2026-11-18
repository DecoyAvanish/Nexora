from datetime import datetime, timezone

from backend.services.fundamental_analysis import FundamentalAnalysisService
from backend.services.sec_edgar import FactObservation, FilingReference


def fact(concept, value, start, end, unit="USD"):
    filing = FilingReference("0001", "10-Q", end, "2026-08-01T16:00:00+00:00", "2026-08-02T16:00:00+00:00", "filing.htm", "https://sec.example/filing.htm")
    return FactObservation(concept, concept, unit, value, start, end, 2026, "Q2", None, filing)


class Sec:
    def point_in_time_facts(self, symbol, as_of):
        observations = [
            fact("RevenueFromContractWithCustomerExcludingAssessedTax", 137, "2026-04-01", "2026-06-30"),
            fact("RevenueFromContractWithCustomerExcludingAssessedTax", 100, "2025-04-01", "2025-06-30"),
            fact("OperatingIncomeLoss", 30, "2026-04-01", "2026-06-30"),
            fact("NetIncomeLoss", 20, "2026-04-01", "2026-06-30"),
            fact("AssetsCurrent", 300, None, "2026-06-30"),
            fact("LiabilitiesCurrent", 150, None, "2026-06-30"),
            fact("StockholdersEquity", 500, None, "2026-06-30"),
        ]
        return {"symbol": symbol, "company_name": "Example", "cik": "1", "as_of": "2026-08-03T00:00:00+00:00", "reporting_lag_hours": 24, "observations": observations}


def test_analysis_computes_metrics_and_preserves_lineage():
    result = FundamentalAnalysisService(Sec()).analyze("TEST", datetime.now(timezone.utc), market_cap=1000)
    assert result["metrics"]["revenue_growth"]["value"] == 37
    assert result["metrics"]["operating_margin"]["value"] == 21.89781
    assert result["metrics"]["current_ratio"]["value"] == 2
    source = result["metrics"]["revenue_growth"]["sources"][0]
    assert source["concept"] == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert source["document_url"] == "https://sec.example/filing.htm"
