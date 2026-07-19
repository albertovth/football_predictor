#!/usr/bin/env python3
"""Fail-closed validation and atomic publication for a rolling update."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--prior-ranking", required=True, type=Path)
    parser.add_argument("--prior-evidence", required=True, type=Path)
    parser.add_argument("--prior-ledger", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--selected-cutoff", required=True, type=float)
    parser.add_argument("--publish", action="store_true")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    shutil.copy2(source, temporary)
    os.replace(temporary, target)


def main() -> int:
    args = parse_args()
    control = json.loads((args.input_dir / "control.json").read_text())
    if control["status"] != "ready":
        raise ValueError("Input evidence gate is not ready.")

    candidate_path = args.run_dir / "output/ranking_final.csv"
    raw_path = args.run_dir / "raw/intermediate/aggregated_xg_data.csv"
    pooled_path = args.run_dir / "intermediate/aggregated_xg_data.csv"
    evidence_path = args.run_dir / "evidence_final.csv"
    ledger_path = args.run_dir / "evidence_ledger_final.csv"
    seeded_one = args.run_dir / "reproducibility/run1/ranking_final.csv"
    seeded_two = args.run_dir / "reproducibility/run2/ranking_final.csv"

    prior = pd.read_csv(args.prior_ranking)
    candidate = pd.read_csv(candidate_path)
    raw = pd.read_csv(raw_path)
    pooled = pd.read_csv(pooled_path)
    results = pd.read_csv(args.input_dir / "results.csv")
    normalization = pd.read_csv(args.input_dir / "goal_median_results.csv")
    evidence = pd.read_csv(evidence_path)
    ledger = pd.read_csv(ledger_path)
    dictionary = pd.read_csv(args.dictionary)
    corrected_to_original = pd.Series(
        dictionary["original"].values, index=dictionary["corrected"]
    ).to_dict()

    checks: dict[str, bool] = {}
    checks["minimum_evidence"] = (
        len(results) == control["eligible_matches"]
        and len(results) >= control["minimum_matches"]
    )
    checks["candidate_universe"] = (
        len(candidate) == 206
        and candidate["name"].nunique() == 206
        and set(candidate["name"]) == set(prior["name"])
    )
    checks["ranks_complete"] = set(candidate["rank"]) == set(range(1, 207))
    checks["metrics_finite"] = (
        np.isfinite(raw[["xG", "xGA", "matches"]].to_numpy()).all()
        and np.isfinite(pooled[["xG", "xGA", "matches"]].to_numpy()).all()
        and (raw[["xG", "xGA", "matches"]] >= 0).all().all()
        and (pooled[["xG", "xGA", "matches"]] >= 0).all().all()
    )
    median_goals = float(
        pd.concat(
            [normalization["home_score"], normalization["away_score"]],
            ignore_index=True,
        ).median()
    )
    checks["normalization_finite"] = np.isfinite(median_goals) and median_goals > 0
    checks["normalization_matches_control"] = (
        len(normalization) == control["normalization_matches"]
        and np.isclose(median_goals, control["median_goals"])
    )
    checks["pooled_medians_match_goals"] = (
        np.isclose(pooled["xG"].median(), median_goals)
        and np.isclose(pooled["xGA"].median(), median_goals)
    )
    checks["new_metric_counts"] = np.isclose(raw["matches"].sum(), 2 * len(results))
    checks["no_new_duplicates"] = not results.duplicated(
        ["date", "home_team", "away_team", "home_score", "away_score", "tournament"]
    ).any()
    ledger_key = [
        "date", "team", "side", "home_team", "away_team",
        "home_score", "away_score", "tournament",
    ]
    checks["no_ledger_duplicates"] = not ledger.duplicated(ledger_key).any()
    checks["evidence_matches_ledger"] = np.isclose(
        evidence["prior_matches"].sum(), len(ledger)
    )
    ledger_dates = pd.to_datetime(ledger["date"])
    checks["rolling_window_exact"] = (
        ledger_dates.min() >= pd.Timestamp(control["evidence_window_start"])
        and ledger_dates.max() <= pd.Timestamp(control["evidence_window_end"])
    )
    checks["seeded_reproducibility"] = sha256(seeded_one) == sha256(seeded_two)
    checks["selected_cutoff_valid"] = (
        np.isfinite(args.selected_cutoff) and 0.01 <= args.selected_cutoff <= 0.25
    )

    # All calibration diagnostics used by the guarded job must be finite.
    calibration_logs = [
        args.run_dir / "logs/02_adjustment_factor.log",
        args.run_dir / "logs/03_caps_off_def.log",
        args.run_dir / "logs/04_low_team_cutoff.log",
        args.run_dir / "logs/05_calculate_raw_xg_xga.log",
        args.run_dir / "logs/06_combine_prior_evidence.log",
    ]
    nonfinite = re.compile(r"(?<![A-Za-z])(?:nan|[+-]?inf)(?![A-Za-z])", re.I)
    checks["calibration_logs_finite"] = all(
        path.exists() and not nonfinite.search(path.read_text(errors="replace"))
        for path in calibration_logs
    )

    # Teams without new matches retain relative prior xG/xGA placement.
    prior_backend = prior.copy()
    prior_backend["team"] = prior_backend["name"].map(
        corrected_to_original
    ).fillna(prior_backend["name"])
    calibration = pd.read_csv(args.run_dir / "evidence_calibration.csv")
    zero = calibration.loc[calibration["new_matches"].eq(0)].merge(
        prior_backend[["team", "off", "def"]], on="team", validate="one_to_one"
    )
    if len(zero):
        off_ratio = zero["xG"] / zero["off"]
        def_ratio = zero["xGA"] / zero["def"]
        checks["zero_match_relative_order"] = (
            np.allclose(off_ratio, off_ratio.iloc[0], rtol=1e-12, atol=1e-12)
            and np.allclose(def_ratio, def_ratio.iloc[0], rtol=1e-12, atol=1e-12)
        )
    else:
        checks["zero_match_relative_order"] = True

    checks["friendly_rule_unchanged"] = (
        "row['home_score'] * 0.5"
        in Path("pipeline/spi_stage2/calculate_xg_xga.py").read_text()
        and "row['away_score'] * 0.5"
        in Path("pipeline/spi_stage2/calculate_xg_xga.py").read_text()
    )

    checks = {name: bool(value) for name, value in checks.items()}
    ready = all(checks.values())
    validation = {
        "publication_ready": ready,
        "checks": checks,
        "control": control,
        "selected_cutoff": args.selected_cutoff,
        "prior_sha256": sha256(args.prior_ranking),
        "candidate_sha256": sha256(candidate_path),
        "seeded_sha256": sha256(seeded_one),
    }
    (args.run_dir / "validation.json").write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )
    if not ready:
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"Publication blocked; failed checks: {failed}")

    if args.publish:
        repo = Path(__file__).resolve().parents[1]
        run_date = pd.Timestamp(control["run_date"])
        dated = f"{run_date.day}_{run_date.month}_{run_date.year}"
        targets = {
            candidate_path: [
                repo / "ranking_final.csv",
                repo / "data/output/ranking_final.csv",
                repo / f"data/config/priors/spi_global_rankings_intl_{dated}.csv",
            ],
            evidence_path: [
                repo / "data/output/ranking_evidence.csv",
                repo / f"data/config/priors/ranking_evidence_{dated}.csv",
            ],
            ledger_path: [
                repo / "data/output/ranking_evidence_ledger.csv",
                repo / f"data/config/priors/ranking_evidence_ledger_{dated}.csv",
            ],
        }
        for source, destinations in targets.items():
            for destination in destinations:
                atomic_copy(source, destination)
        validation["published"] = True
        (args.run_dir / "validation.json").write_text(
            json.dumps(validation, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps(validation, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
