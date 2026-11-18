"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    environment: str
    host: str
    port: int
    allowed_origins: tuple[str, ...]
    finnhub_api_key: str | None
    request_timeout_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            environment=os.getenv("NEXORA_ENV", "development"),
            host=os.getenv("NEXORA_HOST", "127.0.0.1"),
            port=int(os.getenv("NEXORA_PORT", "5001")),
            allowed_origins=_csv(os.getenv("NEXORA_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")),
            finnhub_api_key=os.getenv("FINNHUB_API_KEY") or None,
            request_timeout_seconds=float(os.getenv("NEXORA_REQUEST_TIMEOUT", "10")),
        )
