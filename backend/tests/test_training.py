import pandas as pd

from backend.training.cross_sectional import assign_deciles, prepare_frame


def test_features_are_ranked_cross_sectionally():
    frame = pd.DataFrame({
        "date": ["2026-01-02"] * 3,
        "ticker": ["A", "B", "C"],
        "momentum": [30.0, 10.0, 20.0],
        "fwd_ret_63d": [0.2, -0.1, 0.1],
        "bench_ret_63d": [0.05] * 3,
    })
    prepared, features = prepare_frame(frame)
    assert features == ["momentum"]
    assert prepared.loc[prepared.ticker == "A", "momentum"].iloc[0] == 1.0
    assert prepared["y"].tolist() == [1, 0, 1]


def test_probability_rank_becomes_one_to_ten_score():
    scores = assign_deciles(pd.Series(range(10)))
    assert scores.min() == 1
    assert scores.max() == 10
