from pathlib import Path
import sys

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.stage_config import (
    empirical_median_goals,
    resolve_goal_median_window,
)


def test_goal_median_uses_explicit_longer_window(tmp_path: Path) -> None:
    results = pd.DataFrame(
        [
            {"date": "2022-07-20", "home_score": 0, "away_score": 1},
            {"date": "2025-06-01", "home_score": 1, "away_score": 2},
            {"date": "2026-07-18", "home_score": 6, "away_score": 4},
            {"date": "2026-07-19", "home_score": 1, "away_score": 0},
            {"date": "2026-07-20", "home_score": 99, "away_score": 99},
        ]
    )
    path = tmp_path / "results.csv"
    results.to_csv(path, index=False)

    median = empirical_median_goals(
        path,
        pd.Timestamp("2022-07-20"),
        pd.Timestamp("2026-07-19"),
    )

    assert median == pytest.approx(1.0)


def test_goal_median_window_defaults_to_stage_window(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOAL_MEDIAN_START_DATE", raising=False)
    monkeypatch.delenv("GOAL_MEDIAN_END_DATE", raising=False)
    start, end = resolve_goal_median_window(
        pd.Timestamp("2026-07-16"),
        pd.Timestamp("2026-07-19"),
    )
    assert start == pd.Timestamp("2026-07-16")
    assert end == pd.Timestamp("2026-07-19")


def test_goal_median_window_can_be_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOAL_MEDIAN_START_DATE", "2022-07-20")
    monkeypatch.setenv("GOAL_MEDIAN_END_DATE", "2026-07-19")
    start, end = resolve_goal_median_window(
        pd.Timestamp("2026-07-16"),
        pd.Timestamp("2026-07-19"),
    )
    assert start == pd.Timestamp("2022-07-20")
    assert end == pd.Timestamp("2026-07-19")
