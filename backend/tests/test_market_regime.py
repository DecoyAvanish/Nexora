from datetime import datetime, timezone

import numpy as np

from backend.services.market_data import MarketHistory
from backend.services.market_regime import MarketRegimeService


class Fred:
    values={"VIXCLS":32,"T10Y2Y":-0.4,"BAMLH0A0HYM2":5.8,"ICSA":240000,"CPIAUCSL":310,"FEDFUNDS":5.25}
    def observations(self,series,vintage):
        value=self.values[series]
        return [{"series_id":series,"date":"2026-10-01","value":value,"vintage_start":vintage,"vintage_end":vintage}]


class Market:
    def history(self,symbol,period):
        values=np.linspace(120,90,260) if symbol=="SPY" else np.linspace(120,85,260)
        dates=np.arange("2026-01-01","2027-01-01",dtype="datetime64[D]")[:260].astype(str).tolist()
        data=values.tolist(); return MarketHistory(symbol,dates,data,data,data,data,[1000]*260)


def test_regime_classifies_risk_off_and_preserves_vintage(tmp_path):
    result=MarketRegimeService(Fred(),Market(),tmp_path).classify(datetime(2026,11,18,tzinfo=timezone.utc))
    assert result["state"]=="high_volatility_risk_off"
    assert result["point_in_time"] is True
    assert result["sources"][0]["vintage_start"]=="2026-11-18"
    assert (tmp_path/"2026-11-18.json").exists()


def test_high_beta_stock_receives_larger_risk_off_penalty(tmp_path):
    service=MarketRegimeService(Fred(),Market(),tmp_path)
    stock=Market().history("SPY","1y")
    result=service.adjust_score({"ai_score":8},stock,{"state":"high_volatility_risk_off","label":"High Volatility Risk Off"})
    assert result["adjusted_score"]<result["original_score"]
    assert "Score reduced" in result["explanation"]
