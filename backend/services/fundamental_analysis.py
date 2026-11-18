"""Point-in-time fundamental ratios with auditable SEC lineage."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from typing import Any, Iterable

from .sec_edgar import FactObservation, SecEdgarService


CONCEPTS = {
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "gross_profit": ("GrossProfit",),
    "operating_income": ("OperatingIncomeLoss",),
    "net_income": ("NetIncomeLoss", "ProfitLoss"),
    "cfo": ("NetCashProvidedByUsedInOperatingActivities",),
    "capex": ("PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsForAdditionsToPropertyPlantAndEquipment"),
    "assets": ("Assets",),
    "current_assets": ("AssetsCurrent",),
    "current_liabilities": ("LiabilitiesCurrent",),
    "equity": ("StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    "debt": ("LongTermDebtAndFinanceLeaseObligationsCurrent", "LongTermDebtCurrent", "LongTermDebtNoncurrent", "ShortTermBorrowings"),
    "cash": ("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    "interest": ("InterestExpenseNonOperating", "InterestExpense"),
    "pretax": ("IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"),
    "tax": ("IncomeTaxExpenseBenefit",),
    "shares": ("EntityCommonStockSharesOutstanding", "CommonStocksIncludingAdditionalPaidInCapitalMember", "CommonStockSharesOutstanding"),
}


class FundamentalAnalysisService:
    def __init__(self, sec: SecEdgarService, market_data=None):
        self.sec = sec
        self.market_data = market_data

    def analyze(self, symbol: str, as_of: datetime | None = None, market_cap: float | None = None) -> dict[str, Any]:
        payload = self.sec.point_in_time_facts(symbol, as_of)
        facts = self._deduplicate(payload["observations"])
        latest_quarter = self._latest_period(facts, "quarter")
        prior_year_quarter = self._prior_year_period(facts, latest_quarter)
        previous_quarter = self._previous_period(facts, latest_quarter)
        latest_annual = self._latest_period(facts, "annual")
        current = self._instant_values(facts)
        cap = market_cap or self._market_cap(symbol)

        metrics: dict[str, Any] = {}
        self._growth(metrics, "revenue_growth", latest_quarter, prior_year_quarter, "revenue")
        self._growth(metrics, "earnings_growth", latest_quarter, prior_year_quarter, "net_income")
        self._margin(metrics, "gross_margin", latest_quarter, "gross_profit")
        self._margin(metrics, "operating_margin", latest_quarter, "operating_income")
        self._margin(metrics, "net_margin", latest_quarter, "net_income")
        self._ratio(metrics, "current_ratio", current.get("current_assets"), current.get("current_liabilities"))
        self._ratio(metrics, "debt_to_equity", current.get("debt"), current.get("equity"))
        self._ratio(metrics, "interest_coverage", latest_annual.get("operating_income"), latest_annual.get("interest"))
        self._ratio(metrics, "roe", latest_annual.get("net_income"), current.get("equity"), percent=True)
        invested = self._combined(current, ("debt", "equity"), subtract="cash")
        nopat = self._nopat(latest_annual)
        self._ratio(metrics, "roic", nopat, invested, percent=True)
        fcf = self._difference(latest_annual.get("cfo"), latest_annual.get("capex"), absolute_second=True)
        self._ratio(metrics, "free_cash_flow_yield", fcf, self._synthetic(cap, "MarketCapitalization"), percent=True)
        self._ratio(metrics, "price_to_sales", self._synthetic(cap, "MarketCapitalization"), latest_annual.get("revenue"))
        self._ratio(metrics, "price_to_earnings", self._synthetic(cap, "MarketCapitalization"), latest_annual.get("net_income"))
        self._ratio(metrics, "earnings_quality", latest_annual.get("cfo"), latest_annual.get("net_income"))
        accruals = self._difference(latest_annual.get("net_income"), latest_annual.get("cfo"))
        self._ratio(metrics, "accrual_quality", accruals, current.get("assets"), percent=True)
        self._growth(metrics, "share_dilution", current, self._prior_instant_values(facts, current), "shares")
        self._acceleration(metrics, latest_quarter, previous_quarter, prior_year_quarter)

        drivers = self._drivers(metrics)
        return {
            "symbol": payload["symbol"], "company_name": payload["company_name"], "cik": payload["cik"],
            "as_of": payload["as_of"], "reporting_lag_hours": payload["reporting_lag_hours"],
            "latest_period": latest_quarter.get("_end"), "metrics": metrics, "drivers": drivers,
            "disclaimer": "Fundamental signals are research outputs, not investment advice.",
        }

    @staticmethod
    def _deduplicate(facts: Iterable[FactObservation]) -> list[FactObservation]:
        chosen = {}
        for fact in facts:
            key = (fact.concept, fact.unit, fact.start, fact.end)
            if key not in chosen or fact.filing.accepted_at > chosen[key].filing.accepted_at:
                chosen[key] = fact
        return list(chosen.values())

    def _latest_period(self, facts, kind):
        periods = self._periods(facts, kind)
        return periods[max(periods)] if periods else {}

    def _periods(self, facts, kind):
        periods = {}
        for fact in facts:
            if not fact.start or fact.unit != "USD":
                continue
            days = (date.fromisoformat(fact.end) - date.fromisoformat(fact.start)).days
            if (kind == "quarter" and not 70 <= days <= 110) or (kind == "annual" and not 300 <= days <= 400):
                continue
            bucket = periods.setdefault(fact.end, {"_end": fact.end, "_start": fact.start})
            for name, concepts in CONCEPTS.items():
                if fact.concept in concepts and name not in bucket:
                    bucket[name] = fact
        return periods

    def _prior_year_period(self, facts, latest):
        if not latest: return {}
        target = date.fromisoformat(latest["_end"])
        periods = self._periods(facts, "quarter")
        candidates = [(abs((date.fromisoformat(end) - target).days + 365), value) for end, value in periods.items() if end < latest["_end"]]
        return min(candidates, key=lambda item: item[0])[1] if candidates else {}

    def _previous_period(self, facts, latest):
        periods = self._periods(facts, "quarter")
        ends = sorted(end for end in periods if latest and end < latest["_end"])
        return periods[ends[-1]] if ends else {}

    def _instant_values(self, facts, before=None):
        instants = [f for f in facts if not f.start and (before is None or f.end < before)]
        result = {"_end": max((f.end for f in instants), default=None)}
        for name, concepts in CONCEPTS.items():
            candidates = [f for f in instants if f.concept in concepts]
            if candidates: result[name] = max(candidates, key=lambda f: (f.end, f.filing.accepted_at))
        return result

    def _prior_instant_values(self, facts, current):
        end = current.get("_end")
        if not end: return {}
        target = (date.fromisoformat(end).replace(year=date.fromisoformat(end).year - 1)).isoformat()
        candidates = [f for f in facts if not f.start and f.end <= target]
        return self._instant_values(candidates)

    @staticmethod
    def _source(fact):
        if not fact: return None
        if isinstance(fact, dict): return fact
        if not isinstance(fact, FactObservation): return {"concept": "MarketCapitalization", "value": fact}
        return {"concept": fact.concept, "value": fact.value, "unit": fact.unit, "period_end": fact.end,
                "form": fact.filing.form, "accepted_at": fact.filing.accepted_at,
                "accession_number": fact.filing.accession_number, "document_url": fact.filing.document_url}

    def _set(self, metrics, name, value, inputs):
        metrics[name] = {"value": round(value, 6) if value is not None else None,
                         "status": "available" if value is not None else "unavailable",
                         "sources": [self._source(x) for x in inputs if x is not None]}

    def _growth(self, metrics, name, current, prior, key):
        a, b = current.get(key), prior.get(key)
        value = ((a.value / b.value) - 1) * 100 if a and b and b.value else None
        self._set(metrics, name, value, (a, b))

    def _margin(self, metrics, name, period, numerator): self._ratio(metrics, name, period.get(numerator), period.get("revenue"), percent=True)
    def _ratio(self, metrics, name, numerator, denominator, percent=False):
        a, b = self._value(numerator), self._value(denominator)
        value = a / b * (100 if percent else 1) if a is not None and b not in (None, 0) else None
        self._set(metrics, name, value, (numerator, denominator))
    @staticmethod
    def _value(item): return item.value if isinstance(item, FactObservation) else item.get("value") if isinstance(item, dict) else item
    def _difference(self, a, b, absolute_second=False):
        if a is None or b is None: return None
        value = self._value(a) - (abs(self._value(b)) if absolute_second else self._value(b))
        return {"value": value, "concept": "DerivedDifference"}
    def _combined(self, values, names, subtract=None):
        parts = [values.get(name) for name in names]
        if any(p is None for p in parts): return None
        value = sum(self._value(p) for p in parts) - (self._value(values.get(subtract)) if subtract and values.get(subtract) else 0)
        return {"value": value, "concept": "InvestedCapital"}
    def _nopat(self, annual):
        op, tax, pretax = annual.get("operating_income"), annual.get("tax"), annual.get("pretax")
        if not op: return None
        rate = min(max(self._value(tax) / self._value(pretax), 0), .5) if tax and pretax and self._value(pretax) else .21
        return {"value": self._value(op) * (1 - rate), "concept": "NOPAT"}
    @staticmethod
    def _synthetic(value, concept): return {"value": value, "concept": concept} if value else None
    def _acceleration(self, metrics, latest, previous, prior_year):
        current_growth = ((self._value(latest.get("revenue")) / self._value(prior_year.get("revenue"))) - 1) * 100 if latest.get("revenue") and prior_year.get("revenue") and self._value(prior_year["revenue"]) else None
        sequential = ((self._value(latest.get("revenue")) / self._value(previous.get("revenue"))) - 1) * 100 if latest.get("revenue") and previous.get("revenue") and self._value(previous["revenue"]) else None
        self._set(metrics, "quarter_over_quarter_acceleration", sequential - current_growth if sequential is not None and current_growth is not None else None, (latest.get("revenue"), previous.get("revenue"), prior_year.get("revenue")))
    def _market_cap(self, symbol):
        try:
            import yfinance as yf
            return float(yf.Ticker(symbol).fast_info["market_cap"])
        except Exception: return None
    @staticmethod
    def _drivers(metrics):
        labels = {"revenue_growth": "Revenue growth", "operating_margin": "Operating margin", "free_cash_flow_yield": "Free-cash-flow yield", "share_dilution": "Share count growth", "debt_to_equity": "Debt-to-equity", "earnings_quality": "Cash earnings quality"}
        positive, negative = [], []
        for key, label in labels.items():
            value = metrics.get(key, {}).get("value")
            if value is None: continue
            good = value >= 0 if key not in {"share_dilution", "debt_to_equity"} else value <= 0
            (positive if good else negative).append({"metric": key, "text": f"{label}: {value:.1f}{'%' if key not in {'debt_to_equity', 'earnings_quality'} else 'x'}", "value": value})
        return {"positive": positive[:4], "negative": negative[:4]}
