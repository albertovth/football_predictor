from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.spi_stage3.build_prior_evidence import canonicalize, load_name_maps


def window_start(cutoff_date: str, years: int = 4) -> pd.Timestamp:
    cutoff = pd.Timestamp(cutoff_date)
    return cutoff - pd.DateOffset(years=years) + pd.Timedelta(days=1)


def ranking_teams(path: Path, corrected_to_original: dict[str, str]) -> pd.DataFrame:
    ranking = pd.read_csv(path)
    if "name" in ranking:
        ranking["team"] = canonicalize(ranking["name"], corrected_to_original)
    elif "team" in ranking:
        ranking["team"] = canonicalize(ranking["team"], corrected_to_original)
        ranking["name"] = ranking["team"]
    else:
        raise ValueError("Ranking must contain name or team.")
    if "confed" not in ranking:
        raise ValueError("Ranking must contain confed.")
    if ranking["team"].duplicated().any():
        raise ValueError(f"Duplicate teams in {path}.")
    return ranking[["team", "name", "confed"]].copy()


def parse_segment(value: str) -> tuple[str, pd.Timestamp, pd.Timestamp, Path]:
    parts = value.split("|", 3)
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            "Use LABEL|START_DATE|END_DATE|ELIGIBILITY_PRIOR."
        )
    label, start, end, prior = parts
    start_date = pd.Timestamp(start)
    end_date = pd.Timestamp(end)
    if start_date > end_date:
        raise argparse.ArgumentTypeError(f"Segment starts after it ends: {value}")
    return label, start_date, end_date, Path(prior)


def build_evidence_window(
    results_file: Path,
    dictionary_file: Path,
    current_ranking_file: Path,
    segments: list[tuple[str, pd.Timestamp, pd.Timestamp, Path]],
    cutoff_date: str,
    years: int = 4,
    expected_teams: int = 206,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    corrected_to_original, _ = load_name_maps(dictionary_file)
    current = ranking_teams(current_ranking_file, corrected_to_original)
    if len(current) != expected_teams:
        raise ValueError(f"Expected {expected_teams} current teams, found {len(current)}.")
    current_set = set(current["team"])

    results = pd.read_csv(results_file)
    required = {"date", "home_team", "away_team", "home_score", "away_score"}
    if not required.issubset(results.columns):
        raise ValueError(f"Results must contain {sorted(required)}.")
    if "tournament" not in results:
        results["tournament"] = ""
    results["date"] = pd.to_datetime(results["date"], errors="raise")
    results["home_team"] = canonicalize(results["home_team"], corrected_to_original)
    results["away_team"] = canonicalize(results["away_team"], corrected_to_original)

    cutoff = pd.Timestamp(cutoff_date)
    first_date = window_start(cutoff_date, years)
    ledger_parts: list[pd.DataFrame] = []
    segment_counts: dict[str, int] = {}
    match_key = [
        "date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "tournament",
    ]

    for label, configured_start, configured_end, eligibility_prior in segments:
        start = max(configured_start, first_date)
        end = min(configured_end, cutoff)
        if start > end:
            continue
        eligibility = ranking_teams(eligibility_prior, corrected_to_original)
        eligible_set = set(eligibility["team"])
        rows = results.loc[
            results["date"].between(start, end, inclusive="both")
            & results["home_score"].notna()
            & results["away_score"].notna()
            & results["home_team"].isin(eligible_set)
            & results["away_team"].isin(eligible_set)
        ].copy()
        if rows.duplicated(match_key).any():
            raise ValueError(f"Duplicate eligible matches in {label}.")

        home = rows[match_key].copy()
        home["team"] = home["home_team"]
        home["side"] = "home"
        away = rows[match_key].copy()
        away["team"] = away["away_team"]
        away["side"] = "away"
        appearances = pd.concat([home, away], ignore_index=True)
        appearances = appearances.loc[appearances["team"].isin(current_set)].copy()
        appearances["stage"] = label
        ledger_parts.append(appearances)
        segment_counts[label] = len(appearances)

    if not ledger_parts:
        raise ValueError("No evidence appearances found inside the rolling window.")
    ledger = pd.concat(ledger_parts, ignore_index=True)
    ledger = ledger.merge(current, on="team", how="left", validate="many_to_one")
    ledger["date"] = ledger["date"].dt.strftime("%Y-%m-%d")
    ledger = ledger[
        [
            "date",
            "team",
            "name",
            "confed",
            "stage",
            "side",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "tournament",
        ]
    ].sort_values(["date", "home_team", "away_team", "side"], kind="stable")

    counts = ledger.groupby(["team", "stage"]).size().unstack(fill_value=0)
    evidence = current.merge(counts, on="team", how="left", validate="one_to_one")
    stage_columns: list[str] = []
    for label, *_ in segments:
        if label not in evidence:
            evidence[label] = 0
        column = f"{label}_matches"
        evidence[column] = evidence.pop(label).fillna(0).astype(float)
        stage_columns.append(column)
    evidence["prior_matches"] = evidence[stage_columns].sum(axis=1)
    if (evidence["prior_matches"] <= 0).any():
        missing = evidence.loc[evidence["prior_matches"] <= 0, "team"].tolist()
        raise ValueError(f"Teams without evidence in the rolling window: {missing}")
    evidence["evidence_window_start"] = str(first_date.date())
    evidence["evidence_window_end"] = str(cutoff.date())
    evidence["evidence_window_years"] = years
    evidence = evidence[
        [
            "team",
            "name",
            "confed",
            *stage_columns,
            "prior_matches",
            "evidence_window_start",
            "evidence_window_end",
            "evidence_window_years",
        ]
    ].sort_values(["confed", "team"], kind="stable")

    audit = {
        "method": "four_year_rolling_equal_match_evidence",
        "window_start": str(first_date.date()),
        "window_end": str(cutoff.date()),
        "window_years": years,
        "teams": len(evidence),
        "appearances": len(ledger),
        "minimum_team_appearances": float(evidence["prior_matches"].min()),
        "median_team_appearances": float(evidence["prior_matches"].median()),
        "maximum_team_appearances": float(evidence["prior_matches"].max()),
        "zero_evidence_teams": int((evidence["prior_matches"] == 0).sum()),
        "segment_appearances": segment_counts,
    }
    return ledger.reset_index(drop=True), evidence.reset_index(drop=True), audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a four-year evidence ledger.")
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--current-ranking", type=Path, required=True)
    parser.add_argument("--segment", type=parse_segment, action="append", required=True)
    parser.add_argument("--cutoff-date", required=True)
    parser.add_argument("--years", type=int, default=4)
    parser.add_argument("--expected-teams", type=int, default=206)
    parser.add_argument("--ledger-output", type=Path, required=True)
    parser.add_argument("--evidence-output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ledger, evidence, audit = build_evidence_window(
        results_file=args.results,
        dictionary_file=args.dictionary,
        current_ranking_file=args.current_ranking,
        segments=args.segment,
        cutoff_date=args.cutoff_date,
        years=args.years,
        expected_teams=args.expected_teams,
    )
    for path in [args.ledger_output, args.evidence_output, args.audit_output]:
        path.parent.mkdir(parents=True, exist_ok=True)
    ledger.to_csv(args.ledger_output, index=False)
    evidence.to_csv(args.evidence_output, index=False)
    args.audit_output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
