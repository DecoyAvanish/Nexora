"""Point-in-time FRED/ALFRED access with vintage-safe observations."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from backend.errors import ApiError

FRED_OBSERVATIONS = "https://api.stlouisfed.org/fred/series/observations"


class FredService:
    def __init__(self, api_key: str = "", timeout_seconds: float = 10, cache_root="data/fred_cache", session=None):
        self.api_key, self.timeout_seconds = api_key, timeout_seconds
        self.cache_root, self.session = Path(cache_root), session or requests.Session()

    def observations(self, series_id: str, as_of: date | datetime | str | None = None, limit=400):
        if not self.api_key:
            raise ApiError("Set FRED_API_KEY to enable macroeconomic regime inputs.", 503, "fred_api_key_missing")
        vintage = self._date(as_of)
        cache = self.cache_root / vintage / f"{series_id}.json"
        if cache.is_file(): payload=json.loads(cache.read_text())
        else:
            params={"series_id":series_id,"api_key":self.api_key,"file_type":"json","realtime_start":vintage,"realtime_end":vintage,"observation_end":vintage,"sort_order":"desc","limit":limit}
            try:
                response=self.session.get(FRED_OBSERVATIONS,params=params,timeout=self.timeout_seconds); response.raise_for_status(); payload=response.json()
            except (requests.RequestException,ValueError) as error:
                raise ApiError(f"FRED series {series_id} is temporarily unavailable.",503,"fred_unavailable") from error
            cache.parent.mkdir(parents=True,exist_ok=True); cache.write_text(json.dumps(payload))
        values=[]
        for item in payload.get("observations",[]):
            if item.get("value") in {None,"."}: continue
            values.append({"series_id":series_id,"date":item["date"],"value":float(item["value"]),"vintage_start":item.get("realtime_start"),"vintage_end":item.get("realtime_end")})
        return sorted(values,key=lambda item:item["date"])

    @staticmethod
    def _date(value):
        if value is None:return datetime.now(timezone.utc).date().isoformat()
        if isinstance(value,datetime):return value.date().isoformat()
        if isinstance(value,date):return value.isoformat()
        return str(value)[:10]
