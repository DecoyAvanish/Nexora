"""Point-in-time SEC EDGAR submissions and XBRL company-fact ingestion."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any

import requests

from backend.errors import ApiError
from backend.services.market_data import normalize_symbol

SEC_DATA_ROOT = "https://data.sec.gov"
SEC_ARCHIVES_ROOT = "https://www.sec.gov/Archives/edgar/data"
ALLOWED_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "8-K", "8-K/A"}


@dataclass(frozen=True)
class FilingReference:
    accession_number: str
    form: str
    filing_date: str
    accepted_at: str
    available_at: str
    primary_document: str
    document_url: str


@dataclass(frozen=True)
class FactObservation:
    concept: str
    label: str
    unit: str
    value: float
    start: str | None
    end: str
    fiscal_year: int | None
    fiscal_period: str | None
    frame: str | None
    filing: FilingReference

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "filing": asdict(self.filing)}


class SecEdgarService:
    def __init__(
        self,
        user_agent: str,
        timeout_seconds: float = 15,
        cache_root: Path | str = "data/sec_cache",
        reporting_lag_hours: int = 24,
        session: requests.Session | None = None,
    ):
        if not user_agent or "@" not in user_agent:
            raise ValueError("SEC_USER_AGENT must identify the application and include a contact email.")
        self.timeout_seconds = timeout_seconds
        self.cache_root = Path(cache_root)
        self.reporting_lag_hours = reporting_lag_hours
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"})
        self._lock = Lock()

    def resolve_cik(self, raw_symbol: str) -> tuple[str, str]:
        symbol = normalize_symbol(raw_symbol)
        mapping = self._get_json("https://www.sec.gov/files/company_tickers.json", "company_tickers.json", max_age_hours=24)
        for company in mapping.values():
            if str(company.get("ticker", "")).upper().replace(".", "-") == symbol:
                return str(company["cik_str"]).zfill(10), company.get("title") or symbol
        raise ApiError(f"No SEC registrant was found for {symbol}.", 404, "sec_registrant_not_found")

    def point_in_time_facts(self, raw_symbol: str, as_of: datetime | None = None) -> dict[str, Any]:
        symbol = normalize_symbol(raw_symbol)
        as_of_utc = self._as_utc(as_of or datetime.now(timezone.utc))
        cik, company_name = self.resolve_cik(symbol)
        submissions = self._get_json(f"{SEC_DATA_ROOT}/submissions/CIK{cik}.json", f"submissions-{cik}.json", max_age_hours=6)
        company_facts = self._get_json(f"{SEC_DATA_ROOT}/api/xbrl/companyfacts/CIK{cik}.json", f"companyfacts-{cik}.json", max_age_hours=6)
        filing_map = self._filing_map(cik, submissions)
        observations = []
        for concept, payload in company_facts.get("facts", {}).get("us-gaap", {}).items():
            label = payload.get("label") or concept
            for unit, facts in payload.get("units", {}).items():
                for fact in facts:
                    filing = filing_map.get(fact.get("accn"))
                    if not filing or filing.form not in ALLOWED_FORMS:
                        continue
                    if self._parse_datetime(filing.available_at) > as_of_utc:
                        continue
                    if fact.get("val") is None or not fact.get("end"):
                        continue
                    observations.append(FactObservation(
                        concept=concept,
                        label=label,
                        unit=unit,
                        value=float(fact["val"]),
                        start=fact.get("start"),
                        end=fact["end"],
                        fiscal_year=fact.get("fy"),
                        fiscal_period=fact.get("fp"),
                        frame=fact.get("frame"),
                        filing=filing,
                    ))
        observations.sort(key=lambda item: (item.end, item.filing.accepted_at, item.concept))
        return {
            "symbol": symbol,
            "company_name": company_name,
            "cik": cik,
            "as_of": as_of_utc.isoformat(),
            "reporting_lag_hours": self.reporting_lag_hours,
            "observations": observations,
        }

    def recent_filings(self, raw_symbol: str, limit: int = 25) -> dict[str, Any]:
        symbol = normalize_symbol(raw_symbol)
        cik, company_name = self.resolve_cik(symbol)
        submissions = self._get_json(f"{SEC_DATA_ROOT}/submissions/CIK{cik}.json", f"submissions-{cik}.json", max_age_hours=6)
        filings = sorted(self._filing_map(cik, submissions).values(), key=lambda item: item.accepted_at, reverse=True)
        return {"symbol": symbol, "company_name": company_name, "cik": cik, "filings": [asdict(item) for item in filings[: max(1, min(limit, 100))]]}

    def _filing_map(self, cik: str, submissions: dict[str, Any]) -> dict[str, FilingReference]:
        recent = submissions.get("filings", {}).get("recent", {})
        accessions = recent.get("accessionNumber", [])
        result = {}
        cik_number = str(int(cik))
        for index, accession in enumerate(accessions):
            form = self._item(recent, "form", index)
            if form not in ALLOWED_FORMS:
                continue
            accepted = self._item(recent, "acceptanceDateTime", index) or f"{self._item(recent, 'filingDate', index)}T23:59:59Z"
            accepted_at = self._parse_datetime(accepted)
            available_at = accepted_at + timedelta(hours=self.reporting_lag_hours)
            document = self._item(recent, "primaryDocument", index) or ""
            accession_path = accession.replace("-", "")
            result[accession] = FilingReference(
                accession_number=accession,
                form=form,
                filing_date=self._item(recent, "filingDate", index) or accepted_at.date().isoformat(),
                accepted_at=accepted_at.isoformat(),
                available_at=available_at.isoformat(),
                primary_document=document,
                document_url=f"{SEC_ARCHIVES_ROOT}/{cik_number}/{accession_path}/{document}",
            )
        return result

    def _get_json(self, url: str, cache_name: str, max_age_hours: int) -> dict[str, Any]:
        cache_path = self.cache_root / cache_name
        if cache_path.is_file():
            modified = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=timezone.utc)
            if datetime.now(timezone.utc) - modified < timedelta(hours=max_age_hours):
                return json.loads(cache_path.read_text())
        try:
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            if cache_path.is_file():
                return json.loads(cache_path.read_text())
            raise ApiError("SEC EDGAR data is temporarily unavailable.", 503, "sec_unavailable") from error
        with self._lock:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(payload))
        return payload

    @staticmethod
    def _item(payload: dict[str, list], key: str, index: int):
        values = payload.get(key, [])
        return values[index] if index < len(values) else None

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        text = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return SecEdgarService._as_utc(parsed)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
