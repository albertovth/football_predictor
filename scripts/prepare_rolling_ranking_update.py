#!/usr/bin/env python3
"""Freeze and audit a candidate rolling ranking update.

Exit 0 means the minimum evidence gate passed. Exit 3 means the source was
valid but too few new eligible matches were available; no ranking work should
run. Any other nonzero exit is a hard failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime

import numpy as np
import pandas as pd


MATCH_KEY = [
    "date", "home_team", "away_team", "home_score", "away_score", "tournament"
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--prior-ranking", required=True, type=Path)
    parser.add_argument("--prior-ledger", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--minimum-matches", type=int, default=100)
    parser.add_argument("--run-date")
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    args = parse_args()
    run_date = pd.Timestamp(
        args.run_date
        or datetime.now(ZoneInfo("Europe/Oslo")).date().isoformat()
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    dictionary = pd.read_csv(args.dictionary)
    corrected_to_original = pd.Series(
        dictionary["original"].values, index=dictionary["corrected"]
    ).to_dict()
    original_to_corrected = pd.Series(
        dictionary["corrected"].values, index=dictionary["original"]
    ).to_dict()

    prior = pd.read_csv(args.prior_ranking)
    if len(prior) != 206 or prior["name"].nunique() != 206:
        raise ValueError("Published prior must contain exactly 206 unique teams.")
    prior_backend = prior["name"].map(corrected_to_original).fillna(prior["name"])
    prior_set = set(prior_backend)

    ledger = pd.read_csv(args.prior_ledger)
    ledger["date"] = pd.to_datetime(ledger["date"], errors="raise")
    if ledger.empty:
        raise ValueError("Published evidence ledger is empty.")
    last_included = ledger["date"].max()
    stage_start = last_included + pd.Timedelta(days=1)
    if run_date < stage_start:
        raise ValueError("Run date precedes the next valid stage start.")

    source = pd.read_csv(args.source)
    required = {
        "date", "home_team", "away_team", "home_score", "away_score", "tournament"
    }
    if not required.issubset(source.columns):
        raise ValueError(f"Source is missing columns: {sorted(required - set(source))}")
    source["date"] = pd.to_datetime(source["date"], errors="raise")
    source = source.loc[source["date"].le(run_date)].copy()
    source_snapshot = args.output_dir / "source_results.csv"
    source.assign(date=source["date"].dt.strftime("%Y-%m-%d")).to_csv(
        source_snapshot, index=False
    )

    source["source_home_team"] = source["home_team"]
    source["source_away_team"] = source["away_team"]
    source["home_team"] = source["home_team"].map(corrected_to_original).fillna(
        source["home_team"]
    )
    source["away_team"] = source["away_team"].map(corrected_to_original).fillna(
        source["away_team"]
    )
    period = source.loc[source["date"].between(stage_start, run_date)].copy()
    completed = period.loc[
        period["home_score"].notna() & period["away_score"].notna()
    ].copy()
    eligible_mask = completed["home_team"].isin(prior_set) & completed[
        "away_team"
    ].isin(prior_set)
    eligible = completed.loc[eligible_mask].copy()
    excluded = completed.loc[~eligible_mask].copy()
    excluded["reason"] = np.select(
        [
            ~excluded["home_team"].isin(prior_set)
            & ~excluded["away_team"].isin(prior_set),
            ~excluded["home_team"].isin(prior_set),
        ],
        ["both_teams_outside_prior", "home_team_outside_prior"],
        default="away_team_outside_prior",
    )
    unfinished = period.loc[
        period["home_score"].isna() | period["away_score"].isna()
    ].copy()

    if eligible.duplicated(MATCH_KEY).any():
        raise ValueError("Duplicate eligible matches in the new period.")
    scores = eligible[["home_score", "away_score"]].to_numpy(dtype=float)
    if scores.size and (
        not np.isfinite(scores).all()
        or (scores < 0).any()
        or not np.equal(np.mod(scores, 1), 0).all()
    ):
        raise ValueError("Malformed eligible score found.")

    result_columns = [
        column for column in source.columns
        if column not in {"source_home_team", "source_away_team"}
    ]
    eligible.assign(date=eligible["date"].dt.strftime("%Y-%m-%d"))[
        result_columns
    ].to_csv(args.output_dir / "results.csv", index=False)
    completed.assign(date=completed["date"].dt.strftime("%Y-%m-%d")).to_csv(
        args.output_dir / "all_completed_matches.csv", index=False
    )
    excluded.assign(date=excluded["date"].dt.strftime("%Y-%m-%d")).to_csv(
        args.output_dir / "excluded_matches.csv", index=False
    )
    unfinished.assign(date=unfinished["date"].dt.strftime("%Y-%m-%d")).to_csv(
        args.output_dir / "unfinished_matches.csv", index=False
    )

    mapping_names = sorted(
        set(period["source_home_team"]).union(period["source_away_team"])
    )
    mapping = pd.DataFrame({"source_name": mapping_names})
    mapping["backend_name"] = mapping["source_name"].map(
        corrected_to_original
    ).fillna(mapping["source_name"])
    mapping["ui_name"] = mapping["backend_name"].map(
        original_to_corrected
    ).fillna(mapping["backend_name"])
    mapping["in_prior"] = mapping["backend_name"].isin(prior_set)
    mapping.to_csv(args.output_dir / "name_mapping_audit.csv", index=False)

    window_start = run_date - pd.DateOffset(years=4) + pd.Timedelta(days=1)
    normalization = source.loc[
        source["date"].between(window_start, run_date)
        & source["home_score"].notna()
        & source["away_score"].notna()
    ].copy()
    if normalization.duplicated(MATCH_KEY).any():
        raise ValueError("Duplicate match in the rolling goal-median source.")
    median_goals = pd.concat(
        [normalization["home_score"], normalization["away_score"]],
        ignore_index=True,
    ).median()
    if not np.isfinite(median_goals) or median_goals <= 0:
        raise ValueError(f"Invalid rolling empirical goal median: {median_goals}")
    normalization.assign(date=normalization["date"].dt.strftime("%Y-%m-%d"))[
        result_columns
    ].to_csv(args.output_dir / "goal_median_results.csv", index=False)

    control = {
        "status": "ready" if len(eligible) >= args.minimum_matches else "insufficient",
        "run_date": str(run_date.date()),
        "prior_last_included_match": str(last_included.date()),
        "stage_start": str(stage_start.date()),
        "stage_end": str(run_date.date()),
        "evidence_window_start": str(window_start.date()),
        "evidence_window_end": str(run_date.date()),
        "minimum_matches": args.minimum_matches,
        "eligible_matches": len(eligible),
        "completed_source_rows": len(completed),
        "excluded_rows": len(excluded),
        "unfinished_rows": len(unfinished),
        "friendlies": int(eligible["tournament"].eq("Friendly").sum()),
        "world_cup_matches": int(
            eligible["tournament"].eq("FIFA World Cup").sum()
        ),
        "other_competitive_matches": int(
            (~eligible["tournament"].isin(["Friendly", "FIFA World Cup"])).sum()
        ),
        "normalization_matches": len(normalization),
        "normalization_team_scores": len(normalization) * 2,
        "median_goals": float(median_goals),
        "source": args.source,
        "source_snapshot_sha256": sha256(source_snapshot),
        "results_sha256": sha256(args.output_dir / "results.csv"),
        "goal_median_results_sha256": sha256(
            args.output_dir / "goal_median_results.csv"
        ),
    }
    (args.output_dir / "control.json").write_text(
        json.dumps(control, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(control, indent=2))
    return 0 if control["status"] == "ready" else 3


if __name__ == "__main__":
    raise SystemExit(main())
