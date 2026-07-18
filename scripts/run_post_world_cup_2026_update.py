"""Run the established SPI phase logic on the post-World-Cup sample."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.post_world_cup_update import (
    calculate_ratings,
    calibrate_low_team_cutoff,
    compare_rankings,
    name_maps,
    prepare_confederations,
    prepare_prior,
    simulate_spi,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matches", required=True, type=Path)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--confederations", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--simulations", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--publish", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dictionary = pd.read_csv(args.dictionary)
    name_maps(dictionary)  # Fail before touching outputs if the UI map is unsafe.
    prior_display = pd.read_csv(args.prior)
    prior = prepare_prior(prior_display, dictionary)
    confederations = prepare_confederations(pd.read_csv(args.confederations), dictionary)
    matches = pd.read_csv(args.matches)
    matches["date"] = pd.to_datetime(matches["date"], errors="raise")

    cutoff, cutoff_trials = calibrate_low_team_cutoff(matches, prior)
    run = calculate_ratings(matches, prior, confederations, cutoff)
    ranking = simulate_spi(
        run.ratings,
        dictionary,
        n_simulations=args.simulations,
        seed=args.seed,
    )
    comparison = compare_rankings(prior_display, ranking)

    run.ratings.to_csv(args.output_dir / "aggregated_xg_data.csv", index=False)
    run.opponent_strengths.to_csv(args.output_dir / "opponent_strength_data.csv", index=False)
    ranking.to_csv(args.output_dir / "ranking_final.csv", index=False)
    comparison.to_csv(args.output_dir / "ranking_comparison.csv", index=False)
    cutoff_trials.to_csv(args.output_dir / "low_team_cutoff_trials.csv", index=False)
    with (args.output_dir / "calibration.json").open("w", encoding="utf-8") as stream:
        json.dump(
            {
                **run.calibration,
                "selected_cutoff_quantile": cutoff,
                "cutoff_selection_rule": str(cutoff_trials["selection_rule"].iloc[0]),
            },
            stream,
            indent=2,
        )
    with (args.output_dir / "run_manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(
            {
                "matches": str(args.matches),
                "prior": str(args.prior),
                "dictionary": str(args.dictionary),
                "confederations": str(args.confederations),
                "simulations_per_pair": args.simulations,
                "seed": args.seed,
                "selected_cutoff_quantile": cutoff,
                "selected_cutoff_strength": run.calibration["cutoff_strength"],
                "cutoff_selection_rule": str(cutoff_trials["selection_rule"].iloc[0]),
                "rated_team_count": len(ranking),
                "eligible_match_count": len(run.eligible_matches),
                "published": args.publish,
            },
            stream,
            indent=2,
        )

    if args.publish:
        shutil.copyfile(args.output_dir / "ranking_final.csv", REPO_ROOT / "ranking_final.csv")
        shutil.copyfile(
            args.output_dir / "ranking_final.csv",
            REPO_ROOT / "data/output/ranking_final.csv",
        )

    print(json.dumps({**run.calibration, "selected_cutoff_quantile": cutoff}, indent=2))
    print("\nRanking:")
    print(ranking.to_string(index=False))
    print("\nLargest rises:")
    print(comparison[comparison["status"] == "rated"].nlargest(10, "rank_change").to_string(index=False))
    print("\nLargest falls:")
    print(comparison[comparison["status"] == "rated"].nsmallest(10, "rank_change").to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
