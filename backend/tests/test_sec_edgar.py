from datetime import datetime, timezone

from backend.services.sec_edgar import SecEdgarService


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class Session:
    def __init__(self, payloads):
        self.payloads = payloads
        self.headers = {}

    def get(self, url, timeout):
        return Response(self.payloads[url])


def test_point_in_time_facts_excludes_facts_before_reporting_lag(tmp_path):
    ticker_url = "https://www.sec.gov/files/company_tickers.json"
    submissions_url = "https://data.sec.gov/submissions/CIK0000320193.json"
    facts_url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    submissions = {"filings": {"recent": {
        "accessionNumber": ["0001-26-000001"],
        "form": ["10-Q"],
        "filingDate": ["2026-08-01"],
        "acceptanceDateTime": ["2026-08-01T16:00:00Z"],
        "primaryDocument": ["aapl-10q.htm"],
    }}}
    facts = {"facts": {"us-gaap": {"RevenueFromContractWithCustomerExcludingAssessedTax": {
        "label": "Revenue", "units": {"USD": [{
            "start": "2026-04-01", "end": "2026-06-30", "val": 100,
            "accn": "0001-26-000001", "form": "10-Q", "fy": 2026, "fp": "Q3",
        }]}
    }}}}
    service = SecEdgarService("Nexora tests test@example.com", cache_root=tmp_path, reporting_lag_hours=24, session=Session({
        ticker_url: {"0": {"ticker": "AAPL", "cik_str": 320193, "title": "Apple Inc."}},
        submissions_url: submissions,
        facts_url: facts,
    }))
    before = service.point_in_time_facts("AAPL", datetime(2026, 8, 2, 12, tzinfo=timezone.utc))
    after = service.point_in_time_facts("AAPL", datetime(2026, 8, 3, 12, tzinfo=timezone.utc))
    assert before["observations"] == []
    assert len(after["observations"]) == 1
    observation = after["observations"][0]
    assert observation.filing.accepted_at == "2026-08-01T16:00:00+00:00"
    assert observation.filing.document_url.endswith("/aapl-10q.htm")
