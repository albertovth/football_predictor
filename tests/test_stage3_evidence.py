from pathlib import Path
import sys

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.spi_stage3.build_evidence_window import (
    build_evidence_window,
    window_start,
)
from pipeline.spi_stage3.combine_prior_evidence import (
    combine_prior_evidence,
    rolling_evidence_inputs,
)


def write_csv(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_combination_uses_evidence_and_preserves_zero_match_order(tmp_path: Path) -> None:
    dictionary = write_csv(
        tmp_path / "dictionary.csv",
        [
            {"original": "Alpha", "corrected": "Alpha UI"},
            {"original": "Beta", "corrected": "Beta UI"},
            {"original": "Gamma", "corrected": "Gamma UI"},
        ],
    )
    prior = write_csv(
        tmp_path / "prior.csv",
        [
            {"name": "Alpha UI", "confed": "UEFA", "off": 2.0, "def": 0.5},
            {"name": "Beta UI", "confed": "UEFA", "off": 1.0, "def": 1.0},
            {"name": "Gamma UI", "confed": "UEFA", "off": 0.5, "def": 2.0},
        ],
    )
    evidence = write_csv(
        tmp_path / "evidence.csv",
        [
            {"team": "Alpha", "prior_matches": 9.0},
            {"team": "Beta", "prior_matches": 9.0},
            {"team": "Gamma", "prior_matches": 9.0},
        ],
    )
    new = write_csv(
        tmp_path / "new.csv",
        [
            {"team": "Alpha", "confed": "UEFA", "xG": 4.0, "xGA": 1.0, "matches": 1.0},
            {"team": "Beta", "confed": "UEFA", "xG": 1.0, "xGA": 1.0, "matches": 0.0},
            {"team": "Gamma", "confed": "UEFA", "xG": 0.5, "xGA": 2.0, "matches": 0.0},
        ],
    )

    calibration, aggregated, final_evidence, audit = combine_prior_evidence(
        prior_ranking_file=prior,
        prior_evidence_file=evidence,
        new_metrics_file=new,
        dictionary_file=dictionary,
        median_goals=1.0,
        expected_teams=3,
    )

    alpha = calibration.set_index("team").loc["Alpha"]
    assert alpha["prior_weight"] == pytest.approx(0.9)
    assert alpha["new_weight"] == pytest.approx(0.1)
    assert alpha["pooled_xG_pre_normalization"] == pytest.approx(2.2)
    assert audit["final_off_median"] == pytest.approx(1.0)
    assert audit["final_def_median"] == pytest.approx(1.0)
    assert audit["zero_new_match_teams"] == 2
    assert set(aggregated["team"]) == {"Alpha", "Beta", "Gamma"}
    assert final_evidence.set_index("team").loc["Alpha", "prior_matches"] == 10.0

    no_new = calibration.loc[calibration["new_matches"].eq(0)].set_index("team")
    assert no_new.loc["Beta", "xG"] > no_new.loc["Gamma", "xG"]
    assert no_new.loc["Beta", "xGA"] < no_new.loc["Gamma", "xGA"]


def test_combination_rejects_missing_team_mapping(tmp_path: Path) -> None:
    dictionary = write_csv(
        tmp_path / "dictionary.csv",
        [{"original": "Alpha", "corrected": "Alpha UI"}],
    )
    prior = write_csv(
        tmp_path / "prior.csv",
        [{"name": "Alpha UI", "confed": "UEFA", "off": 1.0, "def": 1.0}],
    )
    evidence = write_csv(
        tmp_path / "evidence.csv",
        [{"team": "Alpha", "prior_matches": 10.0}],
    )
    new = write_csv(
        tmp_path / "new.csv",
        [
            {"team": "Different", "confed": "UEFA", "xG": 1.0, "xGA": 1.0, "matches": 1.0}
        ],
    )

    with pytest.raises(ValueError, match="mapping failure"):
        combine_prior_evidence(
            prior_ranking_file=prior,
            prior_evidence_file=evidence,
            new_metrics_file=new,
            dictionary_file=dictionary,
            median_goals=1.0,
            expected_teams=1,
        )


def test_empty_new_window_reproduces_prior_relative_metrics(tmp_path: Path) -> None:
    dictionary = write_csv(
        tmp_path / "dictionary.csv",
        [
            {"original": "Alpha", "corrected": "Alpha UI"},
            {"original": "Beta", "corrected": "Beta UI"},
            {"original": "Gamma", "corrected": "Gamma UI"},
        ],
    )
    prior = write_csv(
        tmp_path / "prior.csv",
        [
            {"name": "Alpha UI", "confed": "UEFA", "off": 2.0, "def": 0.5},
            {"name": "Beta UI", "confed": "UEFA", "off": 1.0, "def": 1.0},
            {"name": "Gamma UI", "confed": "UEFA", "off": 0.5, "def": 2.0},
        ],
    )
    evidence = write_csv(
        tmp_path / "evidence.csv",
        [
            {"team": "Alpha", "prior_matches": 20.0},
            {"team": "Beta", "prior_matches": 15.0},
            {"team": "Gamma", "prior_matches": 10.0},
        ],
    )
    new = write_csv(
        tmp_path / "new.csv",
        [
            {"team": team, "confed": "UEFA", "xG": 1.0, "xGA": 1.0, "matches": 0.0}
            for team in ["Alpha", "Beta", "Gamma"]
        ],
    )

    _, aggregated, _, audit = combine_prior_evidence(
        prior_ranking_file=prior,
        prior_evidence_file=evidence,
        new_metrics_file=new,
        dictionary_file=dictionary,
        median_goals=1.0,
        expected_teams=3,
    )

    actual = aggregated.set_index("team")
    expected_off = {"Alpha": 2.0, "Beta": 1.0, "Gamma": 0.5}
    expected_def = {"Alpha": 0.5, "Beta": 1.0, "Gamma": 2.0}
    for team in expected_off:
        assert actual.loc[team, "xG"] == pytest.approx(expected_off[team])
        assert actual.loc[team, "xGA"] == pytest.approx(expected_def[team])
    assert audit["zero_new_match_teams"] == 3


def test_four_year_window_is_inclusive_and_uses_historical_universes(
    tmp_path: Path,
) -> None:
    dictionary = write_csv(
        tmp_path / "dictionary.csv",
        [
            {"original": "Alpha", "corrected": "Alpha UI"},
            {"original": "Beta", "corrected": "Beta UI"},
            {"original": "Old Opponent", "corrected": "Old Opponent UI"},
        ],
    )
    current = write_csv(
        tmp_path / "current.csv",
        [
            {"name": "Alpha UI", "confed": "UEFA"},
            {"name": "Beta UI", "confed": "UEFA"},
        ],
    )
    old_prior = write_csv(
        tmp_path / "old_prior.csv",
        [
            {"name": "Alpha UI", "confed": "UEFA"},
            {"name": "Beta UI", "confed": "UEFA"},
            {"name": "Old Opponent UI", "confed": "UEFA"},
        ],
    )
    results = write_csv(
        tmp_path / "results.csv",
        [
            {
                "date": "2022-07-15",
                "home_team": "Alpha",
                "away_team": "Old Opponent",
                "home_score": 1,
                "away_score": 0,
                "tournament": "Test",
            },
            {
                "date": "2022-07-16",
                "home_team": "Alpha",
                "away_team": "Old Opponent",
                "home_score": 1,
                "away_score": 0,
                "tournament": "Test",
            },
            {
                "date": "2026-07-15",
                "home_team": "Alpha",
                "away_team": "Beta",
                "home_score": 1,
                "away_score": 1,
                "tournament": "Test",
            },
        ],
    )

    ledger, evidence, audit = build_evidence_window(
        results_file=results,
        dictionary_file=dictionary,
        current_ranking_file=current,
        segments=[
            (
                "stage1",
                pd.Timestamp("2021-05-26"),
                pd.Timestamp("2026-07-15"),
                old_prior,
            )
        ],
        cutoff_date="2026-07-15",
        years=4,
        expected_teams=2,
    )

    assert window_start("2026-07-15", 4) == pd.Timestamp("2022-07-16")
    assert set(ledger["date"]) == {"2022-07-16", "2026-07-15"}
    counts = evidence.set_index("team")["prior_matches"]
    assert counts["Alpha"] == 2
    assert counts["Beta"] == 1
    assert audit["appearances"] == 3


def test_rolling_update_expires_old_evidence_and_matches_new_counts(
    tmp_path: Path,
) -> None:
    dictionary = write_csv(
        tmp_path / "dictionary.csv",
        [
            {"original": "Alpha", "corrected": "Alpha UI"},
            {"original": "Beta", "corrected": "Beta UI"},
        ],
    )
    prior = write_csv(
        tmp_path / "prior.csv",
        [
            {"name": "Alpha UI", "confed": "UEFA"},
            {"name": "Beta UI", "confed": "UEFA"},
        ],
    )
    ledger_rows = []
    for date in ["2022-07-16", "2023-01-01"]:
        for side, team in [("home", "Alpha"), ("away", "Beta")]:
            ledger_rows.append(
                {
                    "date": date,
                    "team": team,
                    "name": f"{team} UI",
                    "confed": "UEFA",
                    "stage": "old",
                    "side": side,
                    "home_team": "Alpha",
                    "away_team": "Beta",
                    "home_score": 1,
                    "away_score": 1,
                    "tournament": "Test",
                }
            )
    ledger = write_csv(tmp_path / "ledger.csv", ledger_rows)
    results = write_csv(
        tmp_path / "results.csv",
        [
            {
                "date": "2026-07-18",
                "home_team": "Alpha",
                "away_team": "Beta",
                "home_score": 2,
                "away_score": 1,
                "tournament": "Test",
            }
        ],
    )
    metrics = write_csv(
        tmp_path / "metrics.csv",
        [
            {"team": "Alpha", "matches": 1},
            {"team": "Beta", "matches": 1},
        ],
    )

    evidence, updated, audit = rolling_evidence_inputs(
        prior_ledger_file=ledger,
        results_file=results,
        prior_ranking_file=prior,
        new_metrics_file=metrics,
        dictionary_file=dictionary,
        start_date="2026-07-16",
        cutoff_date="2026-07-18",
        stage_label="stage4",
        years=4,
    )

    assert audit["evidence_window_start"] == "2022-07-19"
    assert audit["expired_appearances"] == 2
    assert audit["retained_prior_appearances"] == 2
    assert audit["new_appearances"] == 2
    assert set(updated["date"]) == {"2023-01-01", "2026-07-18"}
    assert evidence.set_index("team").loc["Alpha", "prior_matches"] == 1
