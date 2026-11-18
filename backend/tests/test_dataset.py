import pandas as pd

from backend.training.dataset import BASE_FEATURES, add_cross_sectional_ranks, build_ticker_features


def test_feature_builder_creates_forward_excess_return_inputs():
    dates = pd.date_range("2024-01-01", periods=330, freq="B", tz="UTC")
    prices = pd.DataFrame({
        "Close": [100 + index * 0.2 for index in range(330)],
        "Adj Close": [100 + index * 0.2 for index in range(330)],
        "Volume": [1_000_000 + index for index in range(330)],
    }, index=dates)
    benchmark = pd.Series([100 + index * 0.1 for index in range(330)], index=dates)
    result = build_ticker_features("TEST", prices, benchmark, "Technology")
    assert "fwd_ret_63d" in result
    assert "bench_ret_63d" in result
    assert result["return_252d"].notna().any()


def test_cross_sectional_and_sector_ranks_are_created():
    rows = []
    for ticker, sector, offset in (("A", "Tech", 1), ("B", "Tech", 2), ("C", "Health", 3)):
        row = {"date": "2026-01-02", "ticker": ticker, "sector": sector}
        row.update({feature: offset for feature in BASE_FEATURES})
        rows.append(row)
    ranked, columns = add_cross_sectional_ranks(pd.DataFrame(rows))
    assert len(columns) == len(BASE_FEATURES) * 2
    assert ranked.loc[ranked.ticker == "C", "return_21d_universe_rank"].iloc[0] == 1.0
    assert ranked.loc[ranked.ticker == "B", "return_21d_sector_rank"].iloc[0] == 1.0
