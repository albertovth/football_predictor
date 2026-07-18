from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


STAGE1_START_DATE = "2021-05-26"
STAGE1_END_DATE = "2025-05-26"


def load_name_maps(dictionary_file: Path) -> tuple[dict[str, str], dict[str, str]]:
    dictionary = pd.read_csv(dictionary_file)
    required = {"original", "corrected"}
    if not required.issubset(dictionary.columns):
        raise ValueError(f"Dictionary must contain {sorted(required)}.")
    if dictionary["corrected"].duplicated().any():
        duplicates = dictionary.loc[dictionary["corrected"].duplicated(False), "corrected"].tolist()
        raise ValueError(f"Duplicate UI/corrected names in dictionary: {duplicates}")
    corrected_to_original = pd.Series(
        dictionary["original"].values,
        index=dictionary["corrected"],
    ).to_dict()
    original_to_corrected = pd.Series(
        dictionary["corrected"].values,
        index=dictionary["original"],
    ).to_dict()
    return corrected_to_original, original_to_corrected


def canonicalize(series: pd.Series, corrected_to_original: dict[str, str]) -> pd.Series:
    return series.map(corrected_to_original).fillna(series)


def build_prior_evidence(
    results_file: Path,
    dictionary_file: Path,
    stage1_prior_file: Path,
    stage2_metrics_file: Path,
    stage1_start: str = STAGE1_START_DATE,
    stage1_end: str = STAGE1_END_DATE,
    expected_teams: int = 206,
) -> tuple[pd.DataFrame, dict[str, int | str]]:
    corrected_to_original, original_to_corrected = load_name_maps(dictionary_file)

    results = pd.read_csv(results_file)
    required_results = {"date", "home_team", "away_team", "home_score", "away_score"}
    if not required_results.issubset(results.columns):
        raise ValueError(f"Results must contain {sorted(required_results)}.")
    results["date"] = pd.to_datetime(results["date"], errors="raise")
    results["home_team"] = canonicalize(results["home_team"], corrected_to_original)
    results["away_team"] = canonicalize(results["away_team"], corrected_to_original)

    stage1_prior = pd.read_csv(stage1_prior_file).rename(columns={"name": "team"})
    if "team" not in stage1_prior:
        raise ValueError("Stage 1 prior must contain name or team.")
    stage1_prior["team"] = canonicalize(stage1_prior["team"], corrected_to_original)
    if stage1_prior["team"].duplicated().any():
        raise ValueError("Stage 1 prior contains duplicate backend team names.")
    stage1_universe = set(stage1_prior["team"])

    start = pd.Timestamp(stage1_start)
    end = pd.Timestamp(stage1_end)
    stage1_rows = results.loc[
        results["date"].between(start, end, inclusive="both")
    ].dropna(subset=["home_score", "away_score"])
    stage1_eligible = stage1_rows.loc[
        stage1_rows["home_team"].isin(stage1_universe)
        & stage1_rows["away_team"].isin(stage1_universe)
    ].copy()
    stage1_counts = stage1_eligible["home_team"].value_counts().add(
        stage1_eligible["away_team"].value_counts(),
        fill_value=0,
    )

    stage2 = pd.read_csv(stage2_metrics_file)
    required_stage2 = {"team", "matches", "confed"}
    if not required_stage2.issubset(stage2.columns):
        raise ValueError(f"Stage 2 metrics must contain {sorted(required_stage2)}.")
    stage2["team"] = canonicalize(stage2["team"], corrected_to_original)
    if stage2["team"].duplicated().any():
        raise ValueError("Stage 2 metrics contain duplicate backend team names.")
    if len(stage2) != expected_teams:
        raise ValueError(f"Expected {expected_teams} Stage 2 teams, found {len(stage2)}.")

    evidence = stage2[["team", "confed", "matches"]].rename(
        columns={"matches": "stage2_matches"}
    )
    evidence["stage1_matches"] = evidence["team"].map(stage1_counts).fillna(0.0)
    evidence["stage1_matches"] = evidence["stage1_matches"].astype(float)
    evidence["stage2_matches"] = pd.to_numeric(
        evidence["stage2_matches"], errors="raise"
    ).astype(float)
    evidence["prior_matches"] = (
        evidence["stage1_matches"] + evidence["stage2_matches"]
    )
    if (evidence["prior_matches"] <= 0).any():
        teams = evidence.loc[evidence["prior_matches"] <= 0, "team"].tolist()
        raise ValueError(f"Teams without historical prior evidence: {teams}")
    evidence["name"] = evidence["team"].map(original_to_corrected).fillna(
        evidence["team"]
    )
    evidence = evidence[
        [
            "team",
            "name",
            "confed",
            "stage1_matches",
            "stage2_matches",
            "prior_matches",
        ]
    ].sort_values(["confed", "team"], kind="stable")

    audit = {
        "results_file": str(results_file.resolve()),
        "stage1_start": stage1_start,
        "stage1_end": stage1_end,
        "stage1_prior_teams": len(stage1_universe),
        "stage1_source_completed_rows": len(stage1_rows),
        "stage1_eligible_matches": len(stage1_eligible),
        "stage2_metric_teams": len(stage2),
        "output_teams": len(evidence),
    }
    return evidence.reset_index(drop=True), audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build per-team cumulative Stage 1 + Stage 2 prior evidence."
    )
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--stage1-prior", type=Path, required=True)
    parser.add_argument("--stage2-metrics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path)
    parser.add_argument("--stage1-start", default=STAGE1_START_DATE)
    parser.add_argument("--stage1-end", default=STAGE1_END_DATE)
    parser.add_argument("--expected-teams", type=int, default=206)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    evidence, audit = build_prior_evidence(
        results_file=args.results,
        dictionary_file=args.dictionary,
        stage1_prior_file=args.stage1_prior,
        stage2_metrics_file=args.stage2_metrics,
        stage1_start=args.stage1_start,
        stage1_end=args.stage1_end,
        expected_teams=args.expected_teams,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    evidence.to_csv(args.output, index=False)
    if args.audit_output:
        args.audit_output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([audit]).to_csv(args.audit_output, index=False)
    print(pd.Series(audit).to_string())
    print(f"Saved prior evidence: {args.output.resolve()}")
    print(f"Prior evidence teams: {len(evidence)}")


if __name__ == "__main__":
    main()
