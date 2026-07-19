from pathlib import Path

import pandas as pd

from scripts.validate_and_publish_ranking_update import cutoff_sensitivity_checks


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def test_cutoff_sensitivity_gate_accepts_only_identical_results(tmp_path: Path) -> None:
    metrics = pd.DataFrame(
        {
            "team": ["A", "B"],
            "xG": [1.2, 0.8],
            "xGA": [0.7, 1.3],
            "matches": [4, 3],
        }
    )
    ranking = pd.DataFrame(
        {
            "rank": [1, 2],
            "name": ["A", "B"],
            "confed": ["TEST", "TEST"],
            "off": [1.2, 0.8],
            "def": [0.7, 1.3],
            "spi": [60.0, 40.0],
        }
    )
    selected_pooled = tmp_path / "selected_pooled.csv"
    selected_ranking = tmp_path / "selected_ranking.csv"
    reference_raw = tmp_path / "reference_raw.csv"
    reference_pooled = tmp_path / "reference_pooled.csv"
    reference_ranking = tmp_path / "reference_ranking.csv"
    for path in [selected_pooled, reference_raw, reference_pooled]:
        write_csv(path, metrics)
    for path in [selected_ranking, reference_ranking]:
        write_csv(path, ranking)

    accepted = cutoff_sensitivity_checks(
        selected_pooled, selected_ranking, reference_raw,
        reference_pooled, reference_ranking
    )
    assert all(accepted.values())

    changed_metrics = metrics.copy()
    changed_metrics.loc[1, "xGA"] += 0.001
    write_csv(reference_pooled, changed_metrics)
    rejected_metrics = cutoff_sensitivity_checks(
        selected_pooled, selected_ranking, reference_raw,
        reference_pooled, reference_ranking
    )
    assert not rejected_metrics["cutoff_sensitivity_pooled_identical"]

    write_csv(reference_pooled, metrics)
    changed_ranking = ranking.copy()
    changed_ranking.loc[0, "spi"] += 0.001
    write_csv(reference_ranking, changed_ranking)
    rejected_ranking = cutoff_sensitivity_checks(
        selected_pooled, selected_ranking, reference_raw,
        reference_pooled, reference_ranking
    )
    assert not rejected_ranking["cutoff_sensitivity_seeded_ranking_identical"]


def test_guarded_wrapper_runs_reference_only_for_nonseven_cutoff() -> None:
    wrapper = Path("scripts/run_guarded_ranking_update.sh").read_text()
    assert 'sensitivity_required' in wrapper
    assert 'STAGE2_CUTOFF_QUANTILE="$reference_cutoff"' in wrapper
    assert '--sensitivity-dir "$sensitivity_dir"' in wrapper
