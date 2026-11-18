"""Company-news ingestion using GDELT's free DOC 2.0 API."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import requests

from backend.errors import ApiError
from backend.services.market_data import normalize_symbol

GDELT_DOC_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"


@dataclass(frozen=True)
class NewsArticle:
    title: str
    url: str
    domain: str
    published_at: str | None
    source_country: str | None
    language: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NewsService:
    def __init__(self, timeout_seconds: float = 10, session: requests.Session | None = None):
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "Nexora/1.0"})

    def company_news(
        self,
        raw_symbol: str,
        company_name: str | None = None,
        *,
        days: int = 7,
        limit: int = 25,
    ) -> list[NewsArticle]:
        symbol = normalize_symbol(raw_symbol)
        safe_days = max(1, min(days, 90))
        safe_limit = max(1, min(limit, 75))
        company = (company_name or "").strip()
        query = f'"{company}"' if company and company.upper() != symbol else symbol

        try:
            response = self.session.get(
                GDELT_DOC_ENDPOINT,
                params={
                    "query": f"{query} sourcelang:english",
                    "mode": "ArtList",
                    "maxrecords": safe_limit,
                    "format": "json",
                    "sort": "HybridRel",
                    "timespan": f"{safe_days}d",
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise ApiError("Company news is temporarily unavailable.", 503, "news_unavailable") from error

        articles: list[NewsArticle] = []
        seen_urls: set[str] = set()
        for item in payload.get("articles", []):
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            if not title or not url or url in seen_urls:
                continue
            seen_urls.add(url)
            articles.append(
                NewsArticle(
                    title=title,
                    url=url,
                    domain=str(item.get("domain") or ""),
                    published_at=self._parse_seen_date(item.get("seendate")),
                    source_country=item.get("sourcecountry"),
                    language=item.get("language"),
                )
            )
        return articles

    @staticmethod
    def _parse_seen_date(value: Any) -> str | None:
        if not value:
            return None
        text = str(value)
        for date_format in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
            try:
                parsed = datetime.strptime(text, date_format).replace(tzinfo=timezone.utc)
                return parsed.isoformat()
            except ValueError:
                continue
        return None
