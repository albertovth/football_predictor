from pathlib import Path
import sys

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.spi_stage3.combine_prior_evidence import combine_prior_evidence


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
