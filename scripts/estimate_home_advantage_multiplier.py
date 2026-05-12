import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


SOURCE_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate a simple home-advantage expected-goals multiplier."
    )
    parser.add_argument("--from-date", default="2000-01-01")
    parser.add_argument("--to-date")
    parser.add_argument("--exclude-friendlies", action="store_true")
    parser.add_argument(
        "--output",
        default="data/config/home_advantage_multiplier.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    df = pd.read_csv(SOURCE_URL)
    df["date"] = pd.to_datetime(df["date"])

    from_date = pd.to_datetime(args.from_date)
    df = df[df["date"] >= from_date]

    to_date = None
    if args.to_date:
        to_date = pd.to_datetime(args.to_date)
        df = df[df["date"] <= to_date]

    df = df[df["neutral"] == False]  # noqa: E712

    if args.exclude_friendlies:
        df = df[df["tournament"] != "Friendly"]

    df = df.dropna(subset=["home_score", "away_score"])

    matches_used = int(len(df))
    mean_home_goals = float(df["home_score"].mean())
    mean_away_goals = float(df["away_score"].mean())
    raw_home_away_goal_ratio = mean_home_goals / mean_away_goals
    one_sided_home_lambda_multiplier = raw_home_away_goal_ratio**0.5
    app_multiplier = min(max(one_sided_home_lambda_multiplier, 1.00), 1.30)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "source_url": SOURCE_URL,
        "from_date": args.from_date,
        "to_date": args.to_date,
        "exclude_friendlies": bool(args.exclude_friendlies),
        "matches_used": matches_used,
        "mean_home_goals": mean_home_goals,
        "mean_away_goals": mean_away_goals,
        "raw_home_away_goal_ratio": raw_home_away_goal_ratio,
        "one_sided_home_lambda_multiplier": one_sided_home_lambda_multiplier,
        "app_home_advantage_multiplier": app_multiplier,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "method_note": (
            "Filtered to non-neutral international matches. The raw ratio is "
            "mean(home_score) / mean(away_score). The app multiplier is the "
            "square root of that raw ratio, bounded to [1.00, 1.30], because "
            "the Streamlit app will only boost the selected true home team's "
            "final expected-goals lambda and will not reduce the opponent's "
            "lambda."
        ),
    }

    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("Home-advantage multiplier estimate")
    print(f"Source URL: {SOURCE_URL}")
    print(f"Date range: {args.from_date} to {args.to_date or 'latest'}")
    print(f"Exclude friendlies: {bool(args.exclude_friendlies)}")
    print(f"Matches used: {matches_used}")
    print(f"Mean home goals: {mean_home_goals:.6f}")
    print(f"Mean away goals: {mean_away_goals:.6f}")
    print(f"Raw home/away goal ratio: {raw_home_away_goal_ratio:.6f}")
    print(f"One-sided home lambda multiplier: {one_sided_home_lambda_multiplier:.6f}")
    print(f"Bounded app multiplier: {app_multiplier:.6f}")
    print(f"JSON output path: {output_path}")


if __name__ == "__main__":
    main()
