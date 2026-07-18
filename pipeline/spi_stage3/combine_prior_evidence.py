from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.spi_stage3.build_prior_evidence import canonicalize, load_name_maps
from pipeline.spi_stage3.build_evidence_window import ranking_teams, window_start


CONFEDS = ["CONMEBOL", "UEFA", "CONCACAF", "AFC", "CAF", "OFC"]


def rolling_evidence_inputs(
    prior_ledger_file: Path,
    results_file: Path,
    prior_ranking_file: Path,
    new_metrics_file: Path,
    dictionary_file: Path,
    start_date: str,
    cutoff_date: str,
    stage_label: str,
    years: int = 4,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float | int | str]]:
    """Expire old appearances, append the new stage, and return prior counts."""
    corrected_to_original, _ = load_name_maps(dictionary_file)
    current = ranking_teams(prior_ranking_file, corrected_to_original)
    current_set = set(current["team"])

    prior_ledger = pd.read_csv(prior_ledger_file)
    required_ledger = {
        "date", "team", "name", "confed", "stage", "side",
        "home_team", "away_team", "home_score", "away_score", "tournament",
    }
    if not required_ledger.issubset(prior_ledger.columns):
        raise ValueError(f"Evidence ledger must contain {sorted(required_ledger)}.")
    prior_ledger["date"] = pd.to_datetime(prior_ledger["date"], errors="raise")
    prior_ledger["team"] = canonicalize(prior_ledger["team"], corrected_to_original)
    unexpected_ledger_teams = sorted(set(prior_ledger["team"]) - current_set)
    if unexpected_ledger_teams:
        raise ValueError(
            "Prior evidence ledger contains teams outside the ranking universe: "
            f"{unexpected_ledger_teams}"
        )
    ledger_key = [
        "date", "team", "side", "home_team", "away_team",
        "home_score", "away_score", "tournament",
    ]
    if prior_ledger.duplicated(ledger_key).any():
        raise ValueError("Duplicate team appearances in the prior evidence ledger.")

    stage_start = pd.Timestamp(start_date)
    prior_cutoff = stage_start - pd.Timedelta(days=1)
    cutoff = pd.Timestamp(cutoff_date)
    if cutoff < stage_start:
        raise ValueError("Evidence cutoff precedes the new stage start.")
    if (prior_ledger["date"] > prior_cutoff).any():
        raise ValueError("Prior ledger overlaps the new stage window.")
    first_date = window_start(cutoff_date, years)
    retained_prior = prior_ledger.loc[
        prior_ledger["date"].between(first_date, prior_cutoff, inclusive="both")
    ].copy()

    results = pd.read_csv(results_file)
    required_results = {"date", "home_team", "away_team", "home_score", "away_score"}
    if not required_results.issubset(results.columns):
        raise ValueError(f"Results must contain {sorted(required_results)}.")
    if "tournament" not in results:
        results["tournament"] = ""
    results["date"] = pd.to_datetime(results["date"], errors="raise")
    results["home_team"] = canonicalize(results["home_team"], corrected_to_original)
    results["away_team"] = canonicalize(results["away_team"], corrected_to_original)
    new_rows = results.loc[
        results["date"].between(stage_start, cutoff, inclusive="both")
        & results["home_score"].notna()
        & results["away_score"].notna()
        & results["home_team"].isin(current_set)
        & results["away_team"].isin(current_set)
    ].copy()
    match_key = [
        "date", "home_team", "away_team", "home_score", "away_score", "tournament",
    ]
    if new_rows.duplicated(match_key).any():
        raise ValueError("Duplicate eligible matches in the new evidence window.")
    home = new_rows[match_key].copy()
    home["team"] = home["home_team"]
    home["side"] = "home"
    away = new_rows[match_key].copy()
    away["team"] = away["away_team"]
    away["side"] = "away"
    new_ledger = pd.concat([home, away], ignore_index=True)
    new_ledger["stage"] = stage_label
    new_ledger = new_ledger.merge(current, on="team", how="left", validate="many_to_one")
    ledger_columns = [
        "date", "team", "name", "confed", "stage", "side",
        "home_team", "away_team", "home_score", "away_score", "tournament",
    ]
    new_ledger = new_ledger[ledger_columns]

    metrics = pd.read_csv(new_metrics_file)
    if not {"team", "matches"}.issubset(metrics.columns):
        raise ValueError("New metrics must contain team and matches.")
    metrics["team"] = canonicalize(metrics["team"], corrected_to_original)
    metric_counts = metrics.set_index("team")["matches"].astype(float).reindex(
        current["team"], fill_value=0.0
    )
    ledger_counts = new_ledger["team"].value_counts().reindex(
        current["team"], fill_value=0.0
    )
    if not np.allclose(metric_counts.to_numpy(), ledger_counts.to_numpy()):
        differences = pd.DataFrame({
            "team": current["team"],
            "metric_matches": metric_counts.to_numpy(),
            "ledger_matches": ledger_counts.to_numpy(),
        })
        differences = differences.loc[
            ~np.isclose(differences["metric_matches"], differences["ledger_matches"])
        ]
        raise ValueError(
            "New metric/evidence match-count mismatch:\n" + differences.to_string(index=False)
        )

    prior_counts = retained_prior["team"].value_counts().reindex(
        current["team"], fill_value=0.0
    )
    evidence = current.copy()
    evidence["prior_matches"] = prior_counts.to_numpy(dtype=float)
    if (evidence["prior_matches"] <= 0).any():
        missing = evidence.loc[evidence["prior_matches"] <= 0, "team"].tolist()
        raise ValueError(f"Teams without retained prior evidence: {missing}")
    evidence["evidence_window_start"] = str(first_date.date())
    evidence["prior_evidence_end"] = str(prior_cutoff.date())
    evidence["evidence_window_years"] = years

    combined_ledger = pd.concat(
        [retained_prior[ledger_columns], new_ledger], ignore_index=True
    ).sort_values(["date", "home_team", "away_team", "side"], kind="stable")
    combined_ledger["date"] = pd.to_datetime(combined_ledger["date"]).dt.strftime("%Y-%m-%d")
    audit = {
        "evidence_window_years": years,
        "evidence_window_start": str(first_date.date()),
        "evidence_window_end": str(cutoff.date()),
        "prior_evidence_end": str(prior_cutoff.date()),
        "retained_prior_appearances": len(retained_prior),
        "new_appearances": len(new_ledger),
        "final_appearances": len(combined_ledger),
        "expired_appearances": len(prior_ledger) - len(retained_prior),
    }
    return evidence, combined_ledger.reset_index(drop=True), audit


def empirical_median_goals(
    results_file: Path,
    start_date: str,
    end_date: str,
) -> float:
    results = pd.read_csv(results_file)
    required = {"date", "home_score", "away_score"}
    if not required.issubset(results.columns):
        raise ValueError(f"Results must contain {sorted(required)}.")
    results["date"] = pd.to_datetime(results["date"], errors="raise")
    window = results.loc[
        results["date"].between(
            pd.Timestamp(start_date),
            pd.Timestamp(end_date),
            inclusive="both",
        )
    ]
    median = pd.concat([window["home_score"], window["away_score"]]).median()
    if not np.isfinite(median) or median <= 0:
        raise ValueError(f"Invalid empirical median goals: {median}")
    return float(median)


def combine_prior_evidence(
    prior_ranking_file: Path,
    prior_evidence_file: Path,
    new_metrics_file: Path,
    dictionary_file: Path,
    median_goals: float,
    expected_teams: int = 206,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float | int]]:
    corrected_to_original, original_to_corrected = load_name_maps(dictionary_file)

    prior = pd.read_csv(prior_ranking_file).rename(columns={"name": "team"})
    required_prior = {"team", "confed", "off", "def"}
    if not required_prior.issubset(prior.columns):
        raise ValueError(f"Prior ranking must contain {sorted(required_prior)}.")
    prior["name"] = prior["team"]
    prior["team"] = canonicalize(prior["team"], corrected_to_original)
    if prior["team"].duplicated().any():
        raise ValueError("Prior ranking contains duplicate backend team names.")

    evidence = pd.read_csv(prior_evidence_file)
    required_evidence = {"team", "prior_matches"}
    if not required_evidence.issubset(evidence.columns):
        raise ValueError(f"Prior evidence must contain {sorted(required_evidence)}.")
    evidence["team"] = canonicalize(evidence["team"], corrected_to_original)
    if evidence["team"].duplicated().any():
        raise ValueError("Prior evidence contains duplicate backend team names.")

    new = pd.read_csv(new_metrics_file)
    required_new = {"team", "confed", "xG", "xGA", "matches"}
    if not required_new.issubset(new.columns):
        raise ValueError(f"New metrics must contain {sorted(required_new)}.")
    new["team"] = canonicalize(new["team"], corrected_to_original)
    if new["team"].duplicated().any():
        raise ValueError("New metrics contain duplicate backend team names.")

    if len(prior) != expected_teams:
        raise ValueError(f"Expected {expected_teams} prior teams, found {len(prior)}.")
    if len(evidence) != expected_teams:
        raise ValueError(
            f"Expected {expected_teams} prior-evidence teams, found {len(evidence)}."
        )
    if len(new) != expected_teams:
        raise ValueError(f"Expected {expected_teams} new-metric teams, found {len(new)}.")

    evidence_columns = ["team", "prior_matches"]
    for optional in ["stage1_matches", "stage2_matches"]:
        if optional in evidence:
            evidence_columns.append(optional)

    merged = prior[
        ["team", "name", "confed", "off", "def"]
    ].rename(columns={"confed": "prior_confed"}).merge(
        evidence[evidence_columns],
        on="team",
        how="outer",
        validate="one_to_one",
        indicator="prior_evidence_merge",
    )
    if not merged["prior_evidence_merge"].eq("both").all():
        bad = merged.loc[
            ~merged["prior_evidence_merge"].eq("both"),
            ["team", "prior_evidence_merge"],
        ]
        raise ValueError(f"Prior/evidence mapping failure:\n{bad.to_string(index=False)}")
    merged = merged.drop(columns=["prior_evidence_merge"]).merge(
        new.rename(
            columns={
                "confed": "new_confed",
                "xG": "new_xG",
                "xGA": "new_xGA",
                "matches": "new_matches",
            }
        ),
        on="team",
        how="outer",
        validate="one_to_one",
        indicator="new_merge",
    )
    if not merged["new_merge"].eq("both").all():
        bad = merged.loc[
            ~merged["new_merge"].eq("both"),
            ["team", "new_merge"],
        ]
        raise ValueError(f"Prior/new mapping failure:\n{bad.to_string(index=False)}")
    merged = merged.drop(columns=["new_merge"])

    if not merged["prior_confed"].eq(merged["new_confed"]).all():
        bad = merged.loc[
            ~merged["prior_confed"].eq(merged["new_confed"]),
            ["team", "prior_confed", "new_confed"],
        ]
        raise ValueError(f"Confederation mismatch:\n{bad.to_string(index=False)}")

    numeric = ["off", "def", "prior_matches", "new_xG", "new_xGA", "new_matches"]
    for column in numeric:
        merged[column] = pd.to_numeric(merged[column], errors="raise").astype(float)
    if (merged["prior_matches"] <= 0).any():
        raise ValueError("All prior evidence counts must be positive.")
    if (merged["new_matches"] < 0).any():
        raise ValueError("New match counts cannot be negative.")
    if not np.isfinite(merged[numeric].to_numpy()).all():
        raise ValueError("Non-finite prior, new, or evidence values.")

    prior_off_median = float(merged["off"].median())
    prior_def_median = float(merged["def"].median())
    if prior_off_median <= 0 or prior_def_median <= 0:
        raise ValueError("Prior metric medians must be positive.")
    merged["prior_xG_scaled"] = merged["off"] / prior_off_median * median_goals
    merged["prior_xGA_scaled"] = merged["def"] / prior_def_median * median_goals

    merged["total_matches"] = merged["prior_matches"] + merged["new_matches"]
    merged["prior_weight"] = merged["prior_matches"] / merged["total_matches"]
    merged["new_weight"] = merged["new_matches"] / merged["total_matches"]
    merged["pooled_xG_pre_normalization"] = (
        merged["prior_xG_scaled"] * merged["prior_matches"]
        + merged["new_xG"] * merged["new_matches"]
    ) / merged["total_matches"]
    merged["pooled_xGA_pre_normalization"] = (
        merged["prior_xGA_scaled"] * merged["prior_matches"]
        + merged["new_xGA"] * merged["new_matches"]
    ) / merged["total_matches"]

    pooled_off_median = float(merged["pooled_xG_pre_normalization"].median())
    pooled_def_median = float(merged["pooled_xGA_pre_normalization"].median())
    if pooled_off_median <= 0 or pooled_def_median <= 0:
        raise ValueError("Pooled metric medians must be positive.")
    merged["xG"] = (
        merged["pooled_xG_pre_normalization"] / pooled_off_median * median_goals
    )
    merged["xGA"] = (
        merged["pooled_xGA_pre_normalization"] / pooled_def_median * median_goals
    )
    if not np.isfinite(merged[["xG", "xGA"]].to_numpy()).all():
        raise ValueError("Non-finite final pooled metrics.")
    if (merged[["xG", "xGA"]] < 0).any().any():
        raise ValueError("Negative final pooled metrics.")

    merged["name"] = merged["team"].map(original_to_corrected).fillna(merged["name"])
    calibration_columns = [
        "team",
        "name",
        "prior_confed",
        "prior_matches",
        "new_matches",
        "total_matches",
        "prior_weight",
        "new_weight",
        "off",
        "prior_xG_scaled",
        "new_xG",
        "pooled_xG_pre_normalization",
        "xG",
        "def",
        "prior_xGA_scaled",
        "new_xGA",
        "pooled_xGA_pre_normalization",
        "xGA",
    ]
    for optional in ["stage1_matches", "stage2_matches"]:
        if optional in merged:
            calibration_columns.insert(4, optional)
    calibration = merged[calibration_columns].rename(
        columns={"prior_confed": "confed", "off": "prior_off", "def": "prior_def"}
    )
    aggregated = merged[
        ["team", "xG", "xGA", "total_matches", "new_confed"]
    ].rename(columns={"total_matches": "matches", "new_confed": "confed"})
    final_evidence = merged[
        ["team", "name", "prior_confed", "prior_matches", "new_matches", "total_matches"]
    ].rename(
        columns={
            "prior_confed": "confed",
            "prior_matches": "incoming_prior_matches",
            "new_matches": "stage3_matches",
            "total_matches": "prior_matches",
        }
    )

    audit = {
        "teams": len(aggregated),
        "median_goals": float(median_goals),
        "prior_off_median": prior_off_median,
        "prior_def_median": prior_def_median,
        "pooled_off_median_before_normalization": pooled_off_median,
        "pooled_def_median_before_normalization": pooled_def_median,
        "final_off_median": float(aggregated["xG"].median()),
        "final_def_median": float(aggregated["xGA"].median()),
        "zero_new_match_teams": int((merged["new_matches"] == 0).sum()),
    }
    return calibration, aggregated, final_evidence, audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine current prior metrics and new Stage 3 metrics by evidence."
    )
    parser.add_argument("--prior-ranking", type=Path, required=True)
    parser.add_argument("--prior-evidence", type=Path, required=True)
    parser.add_argument("--new-metrics", type=Path, required=True)
    parser.add_argument("--dictionary", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--aggregated-output", type=Path, required=True)
    parser.add_argument("--confed-output-dir", type=Path, required=True)
    parser.add_argument("--calibration-output", type=Path, required=True)
    parser.add_argument("--evidence-output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path)
    parser.add_argument("--prior-evidence-ledger", type=Path)
    parser.add_argument("--evidence-ledger-output", type=Path)
    parser.add_argument("--windowed-prior-output", type=Path)
    parser.add_argument("--evidence-cutoff-date")
    parser.add_argument("--evidence-window-years", type=int, default=4)
    parser.add_argument("--stage-label", default="stage4")
    parser.add_argument("--expected-teams", type=int, default=206)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rolling_options = [
        args.prior_evidence_ledger,
        args.evidence_ledger_output,
        args.windowed_prior_output,
        args.evidence_cutoff_date,
    ]
    if any(rolling_options) and not all(rolling_options):
        raise ValueError(
            "Rolling evidence requires prior ledger, ledger output, windowed-prior "
            "output, and evidence cutoff date."
        )

    prior_evidence_file = args.prior_evidence
    updated_ledger = None
    window_audit: dict[str, float | int | str] = {}
    if args.prior_evidence_ledger:
        windowed_prior, updated_ledger, window_audit = rolling_evidence_inputs(
            prior_ledger_file=args.prior_evidence_ledger,
            results_file=args.results,
            prior_ranking_file=args.prior_ranking,
            new_metrics_file=args.new_metrics,
            dictionary_file=args.dictionary,
            start_date=args.start_date,
            cutoff_date=args.evidence_cutoff_date,
            stage_label=args.stage_label,
            years=args.evidence_window_years,
        )
        args.windowed_prior_output.parent.mkdir(parents=True, exist_ok=True)
        windowed_prior.to_csv(args.windowed_prior_output, index=False)
        prior_evidence_file = args.windowed_prior_output

    median_goals = empirical_median_goals(
        args.results,
        args.start_date,
        args.end_date,
    )
    calibration, aggregated, final_evidence, audit = combine_prior_evidence(
        prior_ranking_file=args.prior_ranking,
        prior_evidence_file=prior_evidence_file,
        new_metrics_file=args.new_metrics,
        dictionary_file=args.dictionary,
        median_goals=median_goals,
        expected_teams=args.expected_teams,
    )
    if updated_ledger is not None:
        final_evidence = final_evidence.rename(
            columns={"stage3_matches": f"{args.stage_label}_matches"}
        )
        final_evidence["evidence_window_start"] = window_audit[
            "evidence_window_start"
        ]
        final_evidence["evidence_window_end"] = window_audit["evidence_window_end"]
        final_evidence["evidence_window_years"] = window_audit[
            "evidence_window_years"
        ]
        ledger_counts = updated_ledger["team"].value_counts().reindex(
            final_evidence["team"], fill_value=0.0
        )
        if not np.allclose(
            final_evidence["prior_matches"].to_numpy(dtype=float),
            ledger_counts.to_numpy(dtype=float),
        ):
            raise ValueError("Final evidence counts do not equal the dated ledger.")
        audit.update(window_audit)

    args.aggregated_output.parent.mkdir(parents=True, exist_ok=True)
    args.confed_output_dir.mkdir(parents=True, exist_ok=True)
    args.calibration_output.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_output.parent.mkdir(parents=True, exist_ok=True)

    aggregated.to_csv(args.aggregated_output, index=False)
    for confed in CONFEDS:
        confed_data = aggregated.loc[aggregated["confed"].eq(confed)].drop(
            columns=["confed"]
        )
        confed_data.to_csv(args.confed_output_dir / f"{confed}.csv", index=False)
    calibration.to_csv(args.calibration_output, index=False)
    final_evidence.to_csv(args.evidence_output, index=False)
    if updated_ledger is not None:
        args.evidence_ledger_output.parent.mkdir(parents=True, exist_ok=True)
        updated_ledger.to_csv(args.evidence_ledger_output, index=False)
    if args.audit_output:
        args.audit_output.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([audit]).to_csv(args.audit_output, index=False)

    print(pd.Series(audit).to_string())
    print(f"Saved pooled metrics: {args.aggregated_output.resolve()}")
    print(f"Saved calibration: {args.calibration_output.resolve()}")
    print(f"Saved next-stage evidence: {args.evidence_output.resolve()}")


if __name__ == "__main__":
    main()
