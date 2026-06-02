import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
RANKING_FILE = REPO_ROOT / "ranking_final.csv"
HOME_ADVANTAGE_FILE = REPO_ROOT / "data" / "config" / "home_advantage_multiplier.json"
# Parsed from FIFA World Cup 26 Regulations, Annex C.
THIRD_PLACE_ALLOCATION_FILE = REPO_ROOT / "data" / "world_cup_2026_third_place_allocation.json"
CHI2_95_DF2 = 5.991464547107979
HOST_COUNTRIES = {"Mexico": "Mexico", "Canada": "Canada", "USA": "USA"}
NAME_MAP = {
    "United States": "USA",
    "Turkiye": "Turkey",
    "Czechia": "Czech Republic",
    "Cape Verde": "Cape Verde Islands",
    "DR Congo": "Congo DR",
}


GROUPS = {
    "A": ["Mexico", "South Africa", "South Korea", "Czech Republic"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["USA", "Paraguay", "Australia", "Turkey"],
    "E": ["Ivory Coast", "Ecuador", "Germany", "Curacao"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Iran", "New Zealand", "Belgium", "Egypt"],
    "H": ["Saudi Arabia", "Uruguay", "Spain", "Cape Verde Islands"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "Congo DR", "Uzbekistan", "Colombia"],
    "L": ["Ghana", "Panama", "England", "Croatia"],
}


GROUP_FIXTURES = [
    ("A", "Mexico", "South Africa", "Mexico"),
    ("A", "South Korea", "Czech Republic", "Mexico"),
    ("A", "Czech Republic", "South Africa", "USA"),
    ("A", "Mexico", "South Korea", "Mexico"),
    ("A", "Czech Republic", "Mexico", "Mexico"),
    ("A", "South Africa", "South Korea", "Mexico"),
    ("B", "Canada", "Bosnia and Herzegovina", "Canada"),
    ("B", "Qatar", "Switzerland", "USA"),
    ("B", "Switzerland", "Bosnia and Herzegovina", "USA"),
    ("B", "Canada", "Qatar", "Canada"),
    ("B", "Switzerland", "Canada", "Canada"),
    ("B", "Bosnia and Herzegovina", "Qatar", "USA"),
    ("C", "Brazil", "Morocco", "USA"),
    ("C", "Haiti", "Scotland", "USA"),
    ("C", "Scotland", "Morocco", "USA"),
    ("C", "Brazil", "Haiti", "USA"),
    ("C", "Scotland", "Brazil", "USA"),
    ("C", "Morocco", "Haiti", "USA"),
    ("D", "USA", "Paraguay", "USA"),
    ("D", "Australia", "Turkey", "Canada"),
    ("D", "Turkey", "Paraguay", "USA"),
    ("D", "USA", "Australia", "USA"),
    ("D", "Turkey", "USA", "USA"),
    ("D", "Paraguay", "Australia", "USA"),
    ("E", "Ivory Coast", "Ecuador", "USA"),
    ("E", "Germany", "Curacao", "USA"),
    ("E", "Germany", "Ivory Coast", "Canada"),
    ("E", "Ecuador", "Curacao", "USA"),
    ("E", "Curacao", "Ivory Coast", "USA"),
    ("E", "Ecuador", "Germany", "USA"),
    ("F", "Netherlands", "Japan", "USA"),
    ("F", "Sweden", "Tunisia", "Mexico"),
    ("F", "Netherlands", "Sweden", "USA"),
    ("F", "Tunisia", "Japan", "Mexico"),
    ("F", "Japan", "Sweden", "USA"),
    ("F", "Tunisia", "Netherlands", "USA"),
    ("G", "Iran", "New Zealand", "USA"),
    ("G", "Belgium", "Egypt", "USA"),
    ("G", "Belgium", "Iran", "USA"),
    ("G", "New Zealand", "Egypt", "Canada"),
    ("G", "Egypt", "Iran", "USA"),
    ("G", "New Zealand", "Belgium", "Canada"),
    ("H", "Saudi Arabia", "Uruguay", "USA"),
    ("H", "Spain", "Cape Verde Islands", "USA"),
    ("H", "Uruguay", "Cape Verde Islands", "USA"),
    ("H", "Spain", "Saudi Arabia", "USA"),
    ("H", "Cape Verde Islands", "Saudi Arabia", "USA"),
    ("H", "Uruguay", "Spain", "Mexico"),
    ("I", "France", "Senegal", "USA"),
    ("I", "Iraq", "Norway", "USA"),
    ("I", "Norway", "Senegal", "USA"),
    ("I", "France", "Iraq", "USA"),
    ("I", "Norway", "France", "USA"),
    ("I", "Senegal", "Iraq", "Canada"),
    ("J", "Argentina", "Algeria", "USA"),
    ("J", "Austria", "Jordan", "USA"),
    ("J", "Argentina", "Austria", "USA"),
    ("J", "Jordan", "Algeria", "USA"),
    ("J", "Algeria", "Austria", "USA"),
    ("J", "Jordan", "Argentina", "USA"),
    ("K", "Portugal", "Congo DR", "USA"),
    ("K", "Uzbekistan", "Colombia", "Mexico"),
    ("K", "Portugal", "Uzbekistan", "USA"),
    ("K", "Colombia", "Congo DR", "Mexico"),
    ("K", "Colombia", "Portugal", "USA"),
    ("K", "Congo DR", "Uzbekistan", "USA"),
    ("L", "Ghana", "Panama", "Canada"),
    ("L", "England", "Croatia", "USA"),
    ("L", "England", "Ghana", "USA"),
    ("L", "Panama", "Croatia", "Canada"),
    ("L", "Panama", "England", "USA"),
    ("L", "Croatia", "Ghana", "USA"),
]


ROUND_OF_32 = [
    (73, "2A", "2B", "USA"),
    (74, "1E", "3A/B/C/D/F", "USA"),
    (75, "1F", "2C", "Mexico"),
    (76, "1C", "2F", "USA"),
    (77, "1I", "3C/D/F/G/H", "USA"),
    (78, "2E", "2I", "USA"),
    (79, "1A", "3C/E/F/H/I", "Mexico"),
    (80, "1L", "3E/H/I/J/K", "USA"),
    (81, "1D", "3B/E/F/I/J", "USA"),
    (82, "1G", "3A/E/H/I/J", "USA"),
    (83, "2K", "2L", "Canada"),
    (84, "1H", "2J", "USA"),
    (85, "1B", "3E/F/G/I/J", "Canada"),
    (86, "1J", "2H", "USA"),
    (87, "1K", "3D/E/I/J/L", "USA"),
    (88, "2D", "2G", "USA"),
]

THIRD_PLACE_WINNER_SLOTS = ("1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L")


KNOCKOUT_BRACKET = [
    (89, 74, 77, "USA"),
    (90, 73, 75, "USA"),
    (91, 76, 78, "USA"),
    (92, 79, 80, "Mexico"),
    (93, 83, 84, "USA"),
    (94, 81, 82, "USA"),
    (95, 86, 88, "USA"),
    (96, 85, 87, "Canada"),
    (97, 89, 90, "USA"),
    (98, 93, 94, "USA"),
    (99, 91, 92, "USA"),
    (100, 95, 96, "USA"),
    (101, 97, 98, "USA"),
    (102, 99, 100, "USA"),
    (103, ("loser", 101), ("loser", 102), "USA"),
    (104, 101, 102, "USA"),
]


def parse_args():
    parser = argparse.ArgumentParser(description="Simulate the FIFA World Cup 2026.")
    parser.add_argument("--simulations", type=int, default=10000)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--no-home-advantage", action="store_true")
    return parser.parse_args()


def norm_name(name):
    return NAME_MAP.get(name, name)


def load_rankings():
    df = pd.read_csv(RANKING_FILE)
    df.columns = ["rank", "name", "confed", "off", "def", "spi"]
    return df.set_index("name").to_dict("index")


def load_home_multiplier():
    try:
        data = json.loads(HOME_ADVANTAGE_FILE.read_text(encoding="utf-8"))
        return float(data["app_home_advantage_multiplier"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return 1.0


def most_common_score(goals_a, goals_b, mask):
    if not np.any(mask):
        return (0, 0)
    scores = Counter(zip(goals_a[mask].tolist(), goals_b[mask].tolist()))
    return max(scores.items(), key=lambda item: (item[1], -item[0][0], -item[0][1]))[0]


def app_forecast(wins_a, draws, wins_b, n_simulations):
    simulated = [wins_a, draws, wins_b]
    x_list = []
    simulations = range(1, 5000)
    simulations_even = [2 * i for i in simulations]

    expected_sets = (
        [[5000 - (i / 2), 5000 - (i / 2), i] for i in simulations_even if i < 3334]
        + [[5000 - (i / 2), i, 5000 - (i / 2)] for i in simulations_even if i < 3334]
        + [[i, 5000 - (i / 2), 5000 - (i / 2)] for i in simulations_even if i < 3334]
        + [[10000 - (2 * i), i, i] for i in simulations if i > 3333]
        + [[i, 10000 - (2 * i), i] for i in simulations if i > 3333]
        + [[i, i, 10000 - (2 * i)] for i in simulations if i > 3333]
    )

    for expected in expected_sets:
        x_list.append(sum((o - e) ** 2 / e for o, e in zip(simulated, expected)))

    if all(x > CHI2_95_DF2 for x in x_list):
        if wins_a / n_simulations > wins_b / n_simulations + 0.02 and wins_a / n_simulations > draws / n_simulations + 0.02:
            return "team_a"
        if wins_b / n_simulations > wins_a / n_simulations + 0.02 and wins_b / n_simulations > draws / n_simulations + 0.02:
            return "team_b"
    return "draw"


def true_home_team(team_a, team_b, venue_country, use_home_advantage):
    if not use_home_advantage:
        return None
    for team in (team_a, team_b):
        if HOST_COUNTRIES.get(team) == venue_country:
            return team
    return None


def predict_match(team_a, team_b, rankings, n_simulations, venue_country, use_home_advantage, home_multiplier):
    team_a = norm_name(team_a)
    team_b = norm_name(team_b)
    row_a = rankings[team_a]
    row_b = rankings[team_b]
    lambda_a = (row_a["off"] + row_b["def"]) / 2
    lambda_b = (row_b["off"] + row_a["def"]) / 2

    home_team = true_home_team(team_a, team_b, venue_country, use_home_advantage)
    if home_team == team_a:
        lambda_a *= home_multiplier
    elif home_team == team_b:
        lambda_b *= home_multiplier

    goals_a = np.random.poisson(lambda_a, size=n_simulations)
    goals_b = np.random.poisson(lambda_b, size=n_simulations)
    wins_a_mask = goals_a > goals_b
    draws_mask = goals_a == goals_b
    wins_b_mask = goals_a < goals_b
    wins_a = int(np.sum(wins_a_mask))
    draws = int(np.sum(draws_mask))
    wins_b = int(np.sum(wins_b_mask))
    forecast = app_forecast(wins_a, draws, wins_b, n_simulations)

    if forecast == "team_a":
        score = most_common_score(goals_a, goals_b, wins_a_mask)
        winner = team_a
    elif forecast == "team_b":
        score = most_common_score(goals_a, goals_b, wins_b_mask)
        winner = team_b
    else:
        score = most_common_score(goals_a, goals_b, draws_mask)
        winner = None

    return {
        "team_a": team_a,
        "team_b": team_b,
        "lambda_a": lambda_a,
        "lambda_b": lambda_b,
        "score_a": int(score[0]),
        "score_b": int(score[1]),
        "winner": winner,
        "forecast": forecast,
        "wins_a": wins_a,
        "draws": draws,
        "wins_b": wins_b,
        "home_advantage_team": home_team,
    }


def init_table(group):
    return {
        team: {"group": group, "team": team, "played": 0, "wins": 0, "draws": 0, "losses": 0, "gf": 0, "ga": 0, "gd": 0, "points": 0, "spi": 0.0}
        for team in GROUPS[group]
    }


def apply_group_result(table, match, rankings):
    a = match["team_a"]
    b = match["team_b"]
    ga = match["score_a"]
    gb = match["score_b"]
    table[a]["played"] += 1
    table[b]["played"] += 1
    table[a]["gf"] += ga
    table[a]["ga"] += gb
    table[b]["gf"] += gb
    table[b]["ga"] += ga
    table[a]["gd"] = table[a]["gf"] - table[a]["ga"]
    table[b]["gd"] = table[b]["gf"] - table[b]["ga"]
    table[a]["spi"] = rankings[a]["spi"]
    table[b]["spi"] = rankings[b]["spi"]
    if ga > gb:
        table[a]["wins"] += 1
        table[b]["losses"] += 1
        table[a]["points"] += 3
    elif ga < gb:
        table[b]["wins"] += 1
        table[a]["losses"] += 1
        table[b]["points"] += 3
    else:
        table[a]["draws"] += 1
        table[b]["draws"] += 1
        table[a]["points"] += 1
        table[b]["points"] += 1


def sort_table(table):
    return sorted(
        table.values(),
        key=lambda row: (row["points"], row["gd"], row["gf"], row["spi"]),
        reverse=True,
    )


def simulate_groups(rankings, n_simulations, use_home_advantage, home_multiplier):
    tables = {group: init_table(group) for group in GROUPS}
    matches = []
    for group, team_a, team_b, venue_country in GROUP_FIXTURES:
        match = predict_match(team_a, team_b, rankings, n_simulations, venue_country, use_home_advantage, home_multiplier)
        match["group"] = group
        matches.append(match)
        apply_group_result(tables[group], match, rankings)
    standings = {group: sort_table(table) for group, table in tables.items()}
    return matches, standings


def best_thirds(standings):
    thirds = [rows[2] for rows in standings.values()]
    return sorted(thirds, key=lambda row: (row["points"], row["gd"], row["gf"], row["spi"]), reverse=True)[:8]


def third_place_allocation_key(qualified_thirds):
    groups = sorted(row["group"] if isinstance(row, dict) else row for row in qualified_thirds)
    if len(groups) != 8 or len(set(groups)) != 8:
        raise ValueError(f"Expected exactly 8 unique third-place groups, got {groups}")
    invalid = [group for group in groups if group not in GROUPS]
    if invalid:
        raise ValueError(f"Invalid third-place group letters: {invalid}")
    return "".join(groups)


def load_third_place_allocation_table(path=THIRD_PLACE_ALLOCATION_FILE):
    table = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_third_place_allocation_table(table)
    return table


def validate_third_place_allocation_table(table):
    expected_keys = {"".join(groups) for groups in itertools.combinations(GROUPS, 8)}
    if set(table) != expected_keys:
        missing = sorted(expected_keys - set(table))
        extra = sorted(set(table) - expected_keys)
        raise ValueError(f"Invalid Annex C allocation keys. Missing: {missing[:5]}, extra: {extra[:5]}")

    for key, row in table.items():
        if len(key) != 8 or len(set(key)) != 8:
            raise ValueError(f"Invalid Annex C key: {key}")
        if set(row) != set(THIRD_PLACE_WINNER_SLOTS):
            raise ValueError(f"Invalid Annex C winner slots for {key}: {sorted(row)}")

        assigned_groups = []
        for third_slot in row.values():
            if not isinstance(third_slot, str) or len(third_slot) != 2 or not third_slot.startswith("3"):
                raise ValueError(f"Invalid Annex C third-place slot for {key}: {third_slot}")
            assigned_groups.append(third_slot.removeprefix("3"))

        if sorted(assigned_groups) != sorted(key):
            raise ValueError(f"Invalid Annex C row for {key}: assigned groups {assigned_groups}")

        for winner_slot, third_slot in row.items():
            winner_group = winner_slot.removeprefix("1")
            third_group = third_slot.removeprefix("3")
            if winner_group == third_group:
                raise ValueError(f"Invalid Annex C row for {key}: {winner_slot} assigned {third_slot}")


def resolve_third_place_allocation(qualified_thirds, allocation_table=None):
    table = allocation_table or load_third_place_allocation_table()
    key = third_place_allocation_key(qualified_thirds)
    try:
        row = table[key]
    except KeyError as exc:
        raise ValueError(f"Missing FIFA Annex C third-place allocation row for combination {key}") from exc
    return row


def build_slots(standings):
    slots = {}
    for group, rows in standings.items():
        slots[f"1{group}"] = rows[0]["team"]
        slots[f"2{group}"] = rows[1]["team"]
    for row in best_thirds(standings):
        slots[f"3{row['group']}"] = row["team"]
    return slots


def assign_third_slots(slots, qualified_thirds, allocation_table=None):
    allocation = resolve_third_place_allocation(qualified_thirds, allocation_table)
    assignments = {}
    for _, slot_a, slot_b, _ in ROUND_OF_32:
        for slot in (slot_a, slot_b):
            if not slot.startswith("3"):
                continue
            winner_slot = slot_a if slot_b == slot else slot_b
            third_slot = allocation[winner_slot]
            allowed_groups = set(slot.removeprefix("3").split("/"))
            third_group = third_slot.removeprefix("3")
            if third_group not in allowed_groups:
                raise ValueError(f"Invalid Annex C row: {winner_slot} assigned {third_slot}, outside {slot}")
            assignments[slot] = slots[third_slot]
    return assignments


def build_round_of_32_matches(standings, rankings, n_simulations, use_home_advantage, home_multiplier, allocation_table=None):
    slots = build_slots(standings)
    qualified_thirds = best_thirds(standings)
    third_assignments = assign_third_slots(slots, qualified_thirds, allocation_table)
    matches = {}
    losers = {}

    for match_no, slot_a, slot_b, venue_country in ROUND_OF_32:
        team_a = resolve_slot(slot_a, slots, third_assignments)
        team_b = resolve_slot(slot_b, slots, third_assignments)
        match = predict_match(team_a, team_b, rankings, n_simulations, venue_country, use_home_advantage, home_multiplier)
        match["match_no"] = match_no
        match["winner"] = knockout_winner(match)
        match["knockout_tiebreak_note"] = "forecast draw resolved by higher non-draw simulated win count" if match["forecast"] == "draw" else ""
        matches[match_no] = match
        losers[match_no] = match["team_b"] if match["winner"] == match["team_a"] else match["team_a"]

    return matches, losers


def resolve_slot(slot, slots, third_assignments):
    if slot.startswith("3"):
        return third_assignments[slot]
    return slots[slot]


def knockout_winner(match):
    if match["winner"]:
        return match["winner"]
    if match["wins_a"] >= match["wins_b"]:
        return match["team_a"]
    return match["team_b"]


def simulate_knockouts(standings, rankings, n_simulations, use_home_advantage, home_multiplier):
    results, losers = build_round_of_32_matches(standings, rankings, n_simulations, use_home_advantage, home_multiplier)

    for match_no, prev_a, prev_b, venue_country in KNOCKOUT_BRACKET:
        team_a = losers[prev_a[1]] if isinstance(prev_a, tuple) else results[prev_a]["winner"]
        team_b = losers[prev_b[1]] if isinstance(prev_b, tuple) else results[prev_b]["winner"]
        match = predict_match(team_a, team_b, rankings, n_simulations, venue_country, use_home_advantage, home_multiplier)
        match["match_no"] = match_no
        match["winner"] = knockout_winner(match)
        match["knockout_tiebreak_note"] = "forecast draw resolved by higher non-draw simulated win count" if match["forecast"] == "draw" else ""
        results[match_no] = match
        losers[match_no] = match["team_b"] if match["winner"] == match["team_a"] else match["team_a"]

    return results


def print_match(match, prefix=""):
    ha = f" home_adv={match['home_advantage_team']}" if match["home_advantage_team"] else ""
    note = f" ({match['knockout_tiebreak_note']})" if match.get("knockout_tiebreak_note") else ""
    print(
        f"{prefix}{match['team_a']} {match['score_a']}-{match['score_b']} {match['team_b']} "
        f"winner={match['winner'] or 'draw'} forecast={match['forecast']}{ha}{note}"
    )


def main():
    args = parse_args()
    if args.seed is not None:
        np.random.seed(args.seed)

    rankings = load_rankings()
    missing = sorted({team for teams in GROUPS.values() for team in teams if team not in rankings})
    if missing:
        raise SystemExit(f"Missing teams in ranking_final.csv: {', '.join(missing)}")

    home_multiplier = load_home_multiplier()
    use_home_advantage = not args.no_home_advantage
    print(f"World Cup 2026 simulation using {args.simulations} simulations per match")
    print(f"Home advantage: {'on' if use_home_advantage else 'off'} multiplier={home_multiplier:.4f}")
    print("Knockout forecast draws are resolved by higher non-draw simulated win count.")
    print()

    group_matches, standings = simulate_groups(rankings, args.simulations, use_home_advantage, home_multiplier)
    print("GROUP MATCHES")
    for match in group_matches:
        print_match(match, prefix=f"Group {match['group']}: ")

    print("\nGROUP TABLES")
    for group, rows in standings.items():
        print(f"Group {group}")
        for row in rows:
            print(f"  {row['team']}: {row['points']} pts, GD {row['gd']}, GF {row['gf']}")

    print("\nBEST THIRD-PLACE TEAMS")
    for row in best_thirds(standings):
        print(f"  Group {row['group']}: {row['team']} ({row['points']} pts, GD {row['gd']}, GF {row['gf']})")

    knockout_results = simulate_knockouts(standings, rankings, args.simulations, use_home_advantage, home_multiplier)
    print("\nKNOCKOUT MATCHES")
    for match_no in sorted(knockout_results):
        label = "Final" if match_no == 104 else "Third place" if match_no == 103 else f"Match {match_no}"
        print_match(knockout_results[match_no], prefix=f"{label}: ")

    print(f"\nChampion: {knockout_results[104]['winner']}")
    print(f"Third place: {knockout_results[103]['winner']}")


if __name__ == "__main__":
    main()
