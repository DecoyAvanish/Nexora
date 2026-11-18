"""Build point-in-time cross-sectional feature datasets for the S&P 500."""

from __future__ import annotations

import argparse
from io import StringIO
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import requests

SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
BASE_FEATURES = [
    "return_5d", "return_21d", "return_63d", "return_126d", "return_252d",
    "volatility_21d", "volatility_63d", "ma20_ratio", "ma50_ratio", "ma200_ratio",
    "rsi_14", "drawdown_252d", "volume_ratio_20d", "volume_zscore_63d",
]


@dataclass(frozen=True)
class UniverseMember:
    ticker: str
    company: str
    sector: str
    sub_industry: str


def load_sp500_universe(cache_path: Path, refresh: bool = False) -> pd.DataFrame:
    if cache_path.exists() and not refresh:
        universe = pd.read_csv(cache_path)
    else:
        response = requests.get(
            SP500_URL,
            headers={"User-Agent": "Nexora research pipeline (contact: nexora-local)"},
            timeout=30,
        )
        response.raise_for_status()
        table = pd.read_html(StringIO(response.text), attrs={"id": "constituents"})[0]
        universe = table.rename(columns={
            "Symbol": "ticker",
            "Security": "company",
            "GICS Sector": "sector",
            "GICS Sub-Industry": "sub_industry",
        })[["ticker", "company", "sector", "sub_industry"]]
        universe["ticker"] = universe["ticker"].str.replace(".", "-", regex=False)
        universe["membership_as_of"] = date.today().isoformat()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        universe.to_csv(cache_path, index=False)
    required = {"ticker", "company", "sector", "sub_industry"}
    missing = required.difference(universe.columns)
    if missing:
        raise ValueError(f"Universe file is missing: {', '.join(sorted(missing))}")
    return universe.drop_duplicates("ticker").sort_values("ticker").reset_index(drop=True)


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    difference = series.diff()
    gains = difference.clip(lower=0).rolling(window).mean()
    losses = (-difference.clip(upper=0)).rolling(window).mean()
    relative_strength = gains / losses.replace(0, np.nan)
    return (100 - 100 / (1 + relative_strength)).fillna(50)


def build_ticker_features(
    ticker: str,
    prices: pd.DataFrame,
    benchmark_close: pd.Series,
    sector: str,
) -> pd.DataFrame:
    frame = prices.rename(columns=str.lower).copy()
    close_column = "adj close" if "adj close" in frame else "close"
    close = frame[close_column].astype(float)
    volume = frame["volume"].astype(float)
    result = pd.DataFrame(index=frame.index)
    result["ticker"] = ticker
    result["sector"] = sector
    for period in (5, 21, 63, 126, 252):
        result[f"return_{period}d"] = close.pct_change(period)
    daily_return = close.pct_change()
    result["volatility_21d"] = daily_return.rolling(21).std() * np.sqrt(252)
    result["volatility_63d"] = daily_return.rolling(63).std() * np.sqrt(252)
    result["ma20_ratio"] = close / close.rolling(20).mean() - 1
    result["ma50_ratio"] = close / close.rolling(50).mean() - 1
    result["ma200_ratio"] = close / close.rolling(200).mean() - 1
    result["rsi_14"] = _rsi(close)
    result["drawdown_252d"] = close / close.rolling(252, min_periods=126).max() - 1
    result["volume_ratio_20d"] = volume.rolling(20).mean() / volume.rolling(63).mean()
    result["volume_zscore_63d"] = (volume - volume.rolling(63).mean()) / volume.rolling(63).std()
    result["fwd_ret_63d"] = close.shift(-63) / close - 1
    aligned_benchmark = benchmark_close.reindex(result.index).ffill()
    result["bench_ret_63d"] = aligned_benchmark.shift(-63) / aligned_benchmark - 1
    result.index.name = "date"
    return result.reset_index()


def add_cross_sectional_ranks(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    data = frame.copy()
    ranked_columns = []
    for feature in BASE_FEATURES:
        universe_name = f"{feature}_universe_rank"
        sector_name = f"{feature}_sector_rank"
        data[universe_name] = data.groupby("date")[feature].rank(pct=True)
        data[sector_name] = data.groupby(["date", "sector"])[feature].rank(pct=True)
        ranked_columns.extend([universe_name, sector_name])
    return data, ranked_columns


def download_feature_dataset(
    universe: pd.DataFrame,
    start: str,
    end: str | None = None,
    batch_size: int = 75,
) -> pd.DataFrame:
    import yfinance as yf

    benchmark = yf.download("SPY", start=start, end=end, auto_adjust=False, progress=False)
    if benchmark.empty:
        raise RuntimeError("SPY benchmark download returned no data.")
    if isinstance(benchmark.columns, pd.MultiIndex):
        benchmark.columns = benchmark.columns.get_level_values(0)
    benchmark_close = benchmark["Adj Close"] if "Adj Close" in benchmark else benchmark["Close"]
    frames = []
    tickers = universe["ticker"].tolist()
    sector_map = universe.set_index("ticker")["sector"].to_dict()
    for offset in range(0, len(tickers), batch_size):
        batch = tickers[offset : offset + batch_size]
        prices = yf.download(batch, start=start, end=end, auto_adjust=False, progress=False, group_by="ticker", threads=True)
        for ticker in batch:
            try:
                ticker_prices = prices[ticker] if isinstance(prices.columns, pd.MultiIndex) else prices
                if ticker_prices.dropna(how="all").empty:
                    continue
                frames.append(build_ticker_features(ticker, ticker_prices, benchmark_close, sector_map[ticker]))
            except (KeyError, ValueError):
                continue
    if not frames:
        raise RuntimeError("No constituent price histories were downloaded.")
    combined = pd.concat(frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], utc=True)
    combined, _ = add_cross_sectional_ranks(combined)
    return combined.sort_values(["date", "ticker"]).reset_index(drop=True)


def write_dataset(frame: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix == ".parquet":
        frame.to_parquet(output, index=False)
    else:
        frame.to_csv(output, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Nexora's daily S&P 500 feature snapshots.")
    parser.add_argument("--start", default="2018-01-01")
    parser.add_argument("--end")
    parser.add_argument("--universe", type=Path, default=Path("data/sp500_universe.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/features/cross_sectional.csv"))
    parser.add_argument("--refresh-universe", action="store_true")
    args = parser.parse_args()
    universe = load_sp500_universe(args.universe, refresh=args.refresh_universe)
    dataset = download_feature_dataset(universe, args.start, args.end)
    write_dataset(dataset, args.output)
    print(f"Wrote {len(dataset):,} rows for {dataset.ticker.nunique()} stocks to {args.output}")


if __name__ == "__main__":
    main()
