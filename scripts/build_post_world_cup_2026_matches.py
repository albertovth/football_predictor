"""Assemble the post-prior match sample and audit source-name mappings."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.post_world_cup_update import name_maps, prepare_prior


EXPLICIT_SOURCE_ALIASES = {
    # Martj42 renamed this team after the previous snapshot.
    "China": "China PR",
    # football-data.org spellings.
    "Czechia": "Czech Republic",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--martj-results", required=True, type=Path)
    parser.add_argument("--football-data-results", required=True, type=Path)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--dictionary", required=True, type=Path)
    parser.add_argument("--start-date", default="2026-01-27")
    parser.add_argument("--world-cup-start", default="2026-06-11")
    parser.add_argument("--end-date", default="2026-07-19")
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_source_name(value: object) -> tuple[str, str]:
    text = "" if pd.isna(value) else str(value).strip()
    if text in EXPLICIT_SOURCE_ALIASES:
        return EXPLICIT_SOURCE_ALIASES[text], f"explicit:{text}"
    return text, "identity"


def map_api_to_original(value: object, corrected_to_original: dict[str, str]) -> tuple[str, str]:
    text, resolution = canonical_source_name(value)
    if text in corrected_to_original:
        return corrected_to_original[text], (
            f"{resolution};dictionary_corrected:{text}"
            if resolution != "identity"
            else f"dictionary_corrected:{text}"
        )
    return text, resolution


def normalize_martj(path: Path, start: pd.Timestamp, wc_start: pd.Timestamp) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    raw = pd.read_csv(path)
    raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
    selected = raw[
        (raw["date"] >= start)
        & (raw["date"] < wc_start)
        & raw["home_score"].notna()
        & raw["away_score"].notna()
    ].copy()
    mapping_rows: list[dict[str, str]] = []
    for column in ("home_team", "away_team"):
        values = []
        for value in selected[column]:
            mapped, resolution = canonical_source_name(value)
            values.append(mapped)
            mapping_rows.append(
                {
                    "source": "martj42",
                    "source_name": str(value),
                    "canonical_original": mapped,
                    "resolution": resolution,
                }
            )
        selected[column] = values
    selected["source"] = "martj42"
    selected["source_match_id"] = ""
    selected["score_duration"] = "SOURCE_FULL_TIME"
    selected["source_status"] = "FINISHED"
    return selected, mapping_rows


def normalize_football_data(
    path: Path,
    start: pd.Timestamp,
    end: pd.Timestamp,
    corrected_to_original: dict[str, str],
) -> tuple[pd.DataFrame, list[dict[str, str]], list[dict[str, str]]]:
    raw = pd.read_csv(path)
    raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
    required = {"date", "home_score", "away_score", "status", "mapping_error"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Normalized football-data file is missing: {sorted(missing)}")
    reviews = raw[
        (raw["date"] >= start)
        & (raw["date"] <= end)
        & raw["status"].eq("FINISHED")
        & raw["mapping_error"].fillna("").eq("")
        & raw["home_score"].notna()
        & raw["away_score"].notna()
    ].copy()
    incomplete = raw[
        (raw["date"] >= start)
        & (raw["date"] <= end)
        & ~(
            raw["status"].eq("FINISHED")
            & raw["mapping_error"].fillna("").eq("")
            & raw["home_score"].notna()
            & raw["away_score"].notna()
        )
    ]
    mapping_rows: list[dict[str, str]] = []
    for column in ("home_team_source", "away_team_source"):
        target = "home_team" if column.startswith("home") else "away_team"
        values = []
        for value in reviews[column]:
            mapped, resolution = map_api_to_original(value, corrected_to_original)
            values.append(mapped)
            mapping_rows.append(
                {
                    "source": "football_data",
                    "source_name": str(value),
                    "canonical_original": mapped,
                    "resolution": resolution,
                }
            )
        reviews[target] = values
    output = reviews[
        ["date", "home_team", "away_team", "home_score", "away_score", "score_duration"]
    ].copy()
    output["tournament"] = "FIFA World Cup"
    output["city"] = ""
    output["country"] = ""
    output["neutral"] = True
    output["source"] = "football_data"
    output["source_match_id"] = reviews.get("source_match_id", "").astype(str)
    output["source_status"] = reviews["status"].astype(str)
    return output, mapping_rows, incomplete.to_dict("records")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dictionary = pd.read_csv(args.dictionary)
    original_to_corrected, corrected_to_original = name_maps(dictionary)
    prior = prepare_prior(pd.read_csv(args.prior), dictionary)
    prior_teams = set(prior["team"])
    start = pd.Timestamp(args.start_date)
    wc_start = pd.Timestamp(args.world_cup_start)
    end = pd.Timestamp(args.end_date)

    martj, martj_mapping = normalize_martj(args.martj_results, start, wc_start)
    football_data, api_mapping, incomplete = normalize_football_data(
        args.football_data_results, wc_start, end, corrected_to_original
    )
    combined = pd.concat([martj, football_data], ignore_index=True, sort=False)
    combined["date"] = pd.to_datetime(combined["date"]).dt.strftime("%Y-%m-%d")
    combined["home_score"] = combined["home_score"].astype(float)
    combined["away_score"] = combined["away_score"].astype(float)
    key = ["date", "home_team", "away_team"]
    duplicate_rows = combined[combined.duplicated(key, keep=False)].copy()
    if not duplicate_rows.empty:
        raise ValueError(f"Duplicate match keys found:\n{duplicate_rows[key].to_string(index=False)}")

    combined["prior_home_match"] = combined["home_team"].isin(prior_teams)
    combined["prior_away_match"] = combined["away_team"].isin(prior_teams)
    combined["eligible"] = combined["prior_home_match"] & combined["prior_away_match"]
    combined["exclusion_reason"] = ""
    combined.loc[~combined["prior_home_match"], "exclusion_reason"] = "home_missing_prior"
    combined.loc[
        combined["prior_home_match"] & ~combined["prior_away_match"], "exclusion_reason"
    ] = "away_missing_prior"
    combined.loc[
        ~combined["prior_home_match"] & ~combined["prior_away_match"], "exclusion_reason"
    ] = "both_missing_prior"

    mapping_rows = martj_mapping + api_mapping
    mapping_audit = pd.DataFrame(mapping_rows).drop_duplicates()
    mapping_audit["matched_prior"] = mapping_audit["canonical_original"].isin(prior_teams)
    mapping_audit["display_name"] = mapping_audit["canonical_original"].map(
        original_to_corrected
    ).fillna(mapping_audit["canonical_original"])
    mapping_audit = mapping_audit.sort_values(
        ["matched_prior", "source", "source_name"], ascending=[True, True, True]
    )

    combined.to_csv(args.output_dir / "all_completed_matches.csv", index=False)
    combined[combined["eligible"]].to_csv(args.output_dir / "eligible_matches.csv", index=False)
    combined[~combined["eligible"]].to_csv(args.output_dir / "excluded_matches.csv", index=False)
    mapping_audit.to_csv(args.output_dir / "name_mapping_audit.csv", index=False)
    with (args.output_dir / "incomplete_football_data.json").open("w", encoding="utf-8") as stream:
        json.dump(incomplete, stream, indent=2, default=str)

    manifest = {
        "start_date": args.start_date,
        "end_date": args.end_date,
        "world_cup_start": args.world_cup_start,
        "martj_results": str(args.martj_results),
        "martj_sha256": sha256(args.martj_results),
        "football_data_results": str(args.football_data_results),
        "football_data_sha256": sha256(args.football_data_results),
        "prior": str(args.prior),
        "prior_team_count": len(prior_teams),
        "martj_completed_matches": len(martj),
        "football_data_completed_matches": len(football_data),
        "all_completed_matches": len(combined),
        "eligible_matches": int(combined["eligible"].sum()),
        "excluded_matches": int((~combined["eligible"]).sum()),
        "friendly_matches": int(combined.loc[combined["eligible"], "tournament"].eq("Friendly").sum()),
        "world_cup_matches": int(
            combined.loc[combined["eligible"], "tournament"].eq("FIFA World Cup").sum()
        ),
        "other_competitive_matches": int(
            (
                combined["eligible"]
                & ~combined["tournament"].isin(["Friendly", "FIFA World Cup"])
            ).sum()
        ),
        "duplicate_rows": int(len(duplicate_rows)),
        "incomplete_api_rows": len(incomplete),
    }
    with (args.output_dir / "manifest.json").open("w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
    print(json.dumps(manifest, indent=2))
    print("\nExcluded matches:")
    print(combined.loc[~combined["eligible"], key + ["exclusion_reason"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
