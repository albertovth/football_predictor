from pathlib import Path
import json
import subprocess
import sys

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
PREPARE = REPO_ROOT / "scripts/prepare_rolling_ranking_update.py"


def build_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    teams = [f"Team {index}" for index in range(206)]
    prior = tmp_path / "prior.csv"
    pd.DataFrame(
        {
            "rank": range(1, 207),
            "name": teams,
            "confed": "TEST",
            "off": 1.0,
            "def": 1.0,
            "spi": 50.0,
        }
    ).to_csv(prior, index=False)
    dictionary = tmp_path / "dictionary.csv"
    pd.DataFrame({"original": teams, "corrected": teams}).to_csv(
        dictionary, index=False
    )
    ledger = tmp_path / "ledger.csv"
    pd.DataFrame([{"date": "2026-01-31"}]).to_csv(ledger, index=False)
    source = tmp_path / "source.csv"
    pd.DataFrame(
        [
            {
                "date": "2026-02-10",
                "home_team": "Team 0",
                "away_team": "Team 1",
                "home_score": 1,
                "away_score": 0,
                "tournament": "Test Cup",
            },
            {
                "date": "2026-02-11",
                "home_team": "External",
                "away_team": "Team 2",
                "home_score": 2,
                "away_score": 0,
                "tournament": "Test Cup",
            },
            {
                "date": "2026-02-28",
                "home_team": "Team 3",
                "away_team": "Team 4",
                "home_score": None,
                "away_score": None,
                "tournament": "Test Cup",
            },
        ]
    ).to_csv(source, index=False)
    return source, prior, ledger, dictionary


def run_prepare(
    source: Path,
    prior: Path,
    ledger: Path,
    dictionary: Path,
    output: Path,
    minimum: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(PREPARE),
            "--source",
            str(source),
            "--prior-ranking",
            str(prior),
            "--prior-ledger",
            str(ledger),
            "--dictionary",
            str(dictionary),
            "--output-dir",
            str(output),
            "--minimum-matches",
            str(minimum),
            "--run-date",
            "2026-02-28",
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_prepare_rolls_window_to_run_date_and_enforces_evidence_gate(
    tmp_path: Path,
) -> None:
    source, prior, ledger, dictionary = build_inputs(tmp_path)
    insufficient_dir = tmp_path / "insufficient"
    insufficient = run_prepare(
        source, prior, ledger, dictionary, insufficient_dir, minimum=2
    )
    assert insufficient.returncode == 3
    control = json.loads((insufficient_dir / "control.json").read_text())
    assert control["status"] == "insufficient"
    assert control["eligible_matches"] == 1
    assert control["evidence_window_start"] == "2022-03-01"
    assert control["evidence_window_end"] == "2026-02-28"
    assert control["excluded_rows"] == 1
    assert control["unfinished_rows"] == 1

    ready_dir = tmp_path / "ready"
    ready = run_prepare(source, prior, ledger, dictionary, ready_dir, minimum=1)
    assert ready.returncode == 0
    ready_control = json.loads((ready_dir / "control.json").read_text())
    assert ready_control["status"] == "ready"
    results = pd.read_csv(ready_dir / "results.csv")
    assert list(results[["home_team", "away_team"]].iloc[0]) == [
        "Team 0",
        "Team 1",
    ]
