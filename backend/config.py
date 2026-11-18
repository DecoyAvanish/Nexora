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
    request_timeout_seconds: float
    model_artifact_root: str
    sec_user_agent: str
    sec_reporting_lag_hours: int
    firebase_web_api_key: str = ""
    paper_db_path: str = "data/paper_trading.db"
    paper_starting_cash: float = 100000
    paper_slippage_bps: float = 5
    paper_commission: float = 0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            environment=os.getenv("NEXORA_ENV", "development"),
            host=os.getenv("NEXORA_HOST", "127.0.0.1"),
            port=int(os.getenv("NEXORA_PORT", "5001")),
            allowed_origins=_csv(os.getenv("NEXORA_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")),
            request_timeout_seconds=float(os.getenv("NEXORA_REQUEST_TIMEOUT", "10")),
            model_artifact_root=os.getenv("NEXORA_MODEL_ARTIFACT_ROOT", "artifacts/cross_sectional"),
            sec_user_agent=os.getenv("SEC_USER_AGENT", "Nexora research avanishpakalapati@gmail.com"),
            sec_reporting_lag_hours=int(os.getenv("SEC_REPORTING_LAG_HOURS", "24")),
            firebase_web_api_key=os.getenv("FIREBASE_WEB_API_KEY", os.getenv("REACT_APP_FIREBASE_API_KEY", "AIzaSyAil3clxr5vGlTNpC7qux7s8kUEt2mC-Fk")),
            paper_db_path=os.getenv("NEXORA_PAPER_DB", "data/paper_trading.db"),
            paper_starting_cash=float(os.getenv("NEXORA_PAPER_STARTING_CASH", "100000")),
            paper_slippage_bps=float(os.getenv("NEXORA_PAPER_SLIPPAGE_BPS", "5")),
            paper_commission=float(os.getenv("NEXORA_PAPER_COMMISSION", "0")),
        )
