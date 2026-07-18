from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from football_predictor.stage_config import (
    DEFAULT_MAX_GOAL_LIMIT,
    DEFAULT_STAGE2_STRENGTH_LOWER,
    DEFAULT_STAGE2_STRENGTH_UPPER,
    add_strength,
    estimate_stage_metric_parameters,
)


FRIENDLY_WEIGHT = 0.5
ADJUSTED_GOAL_CAP = 6.0
LOW_TEAM_DEFENSIVE_PENALTY_CAP = 6.0
MINIMUM_OFFENSIVE_REWARD = 0.01
CONFEDERATION_ORDER = ("CONMEBOL", "UEFA", "CONCACAF", "AFC", "CAF", "OFC")


@dataclass(frozen=True)
class RatingRun:
    ratings: pd.DataFrame
    opponent_strengths: pd.DataFrame
    calibration: dict[str, float | int]
    eligible_matches: pd.DataFrame


def name_maps(dictionary: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    required = {"original", "corrected"}
    missing = required.difference(dictionary.columns)
    if missing:
        raise ValueError(f"Dictionary is missing columns: {sorted(missing)}")
    if dictionary["original"].duplicated().any():
        raise ValueError("Dictionary has duplicate original names.")
    if dictionary["corrected"].duplicated().any():
        raise ValueError("Dictionary has duplicate corrected names.")
    original_to_corrected = dict(zip(dictionary["original"], dictionary["corrected"]))
    corrected_to_original = dict(zip(dictionary["corrected"], dictionary["original"]))
    return original_to_corrected, corrected_to_original


def prepare_prior(prior: pd.DataFrame, dictionary: pd.DataFrame) -> pd.DataFrame:
    required = {"name", "confed", "off", "def", "spi"}
    missing = required.difference(prior.columns)
    if missing:
        raise ValueError(f"Prior is missing columns: {sorted(missing)}")
    _, corrected_to_original = name_maps(dictionary)
    prepared = prior.copy()
    prepared["display_name"] = prepared["name"]
    prepared["team"] = prepared["name"].map(corrected_to_original).fillna(prepared["name"])
    if prepared["team"].duplicated().any():
        duplicates = prepared.loc[prepared["team"].duplicated(False), "team"].tolist()
        raise ValueError(f"Prior names collide after canonicalization: {duplicates}")
    prepared = add_strength(
        prepared,
        spi_col="spi",
        lower=DEFAULT_STAGE2_STRENGTH_LOWER,
        upper=DEFAULT_STAGE2_STRENGTH_UPPER,
    )
    return prepared


def prepare_confederations(
    confederations: pd.DataFrame,
    dictionary: pd.DataFrame,
) -> pd.DataFrame:
    if len(confederations.columns) < 2:
        raise ValueError("Confederation table must have team and confed columns.")
    _, corrected_to_original = name_maps(dictionary)
    prepared = confederations.iloc[:, :2].copy()
    prepared.columns = ["team", "confed"]
    prepared["team"] = prepared["team"].map(corrected_to_original).fillna(prepared["team"])
    conflicts = prepared.groupby("team")["confed"].nunique()
    conflicts = conflicts[conflicts > 1]
    if not conflicts.empty:
        raise ValueError(f"Confederation conflicts: {conflicts.index.tolist()}")
    return prepared.drop_duplicates("team")


def apply_goal_weights(matches: pd.DataFrame) -> pd.DataFrame:
    weighted = matches.copy()
    weighted[["home_score", "away_score"]] = weighted[["home_score", "away_score"]].astype(float)
    friendly = weighted["tournament"].eq("Friendly")
    weighted.loc[friendly, ["home_score", "away_score"]] *= FRIENDLY_WEIGHT
    return weighted


def _eligible_matches(matches: pd.DataFrame, prior: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "home_team", "away_team", "home_score", "away_score", "tournament"}
    missing = required.difference(matches.columns)
    if missing:
        raise ValueError(f"Matches are missing columns: {sorted(missing)}")
    complete = matches.dropna(subset=["home_score", "away_score"]).copy()
    teams = set(prior["team"])
    return complete[
        complete["home_team"].isin(teams) & complete["away_team"].isin(teams)
    ].copy()


def _score_adjusted_metrics(
    weighted_matches: pd.DataFrame,
    prior: pd.DataFrame,
    cutoff_strength: float,
    adjustment_factor: float,
    dynamism_variable: float,
    *,
    diagnostic_low_defense_floor: bool,
) -> tuple[pd.DataFrame, float]:
    strengths = prior.set_index("team")["strength"]
    minimum_strength = float(prior["strength"].min())
    maximum_strength = float(prior["strength"].max())
    median_strength = float(prior["strength"].median())
    high_teams = set(prior.loc[prior["strength"] >= cutoff_strength, "team"])
    low_team_p_c = max(
        adjustment_factor
        * (
            median_strength / (minimum_strength - dynamism_variable)
            - (maximum_strength + dynamism_variable) / cutoff_strength
        ),
        MINIMUM_OFFENSIVE_REWARD,
    )

    attack = {team: 0.0 for team in prior["team"]}
    defense = {team: 0.0 for team in prior["team"]}

    for row in weighted_matches.itertuples(index=False):
        home = row.home_team
        away = row.away_team
        home_strength = float(strengths[home])
        away_strength = float(strengths[away])

        if home in high_teams and away in high_teams:
            home_attack = row.home_score * adjustment_factor * (
                away_strength / (minimum_strength - dynamism_variable)
            ) - adjustment_factor * row.home_score * (
                (maximum_strength + dynamism_variable) / home_strength
            )
            away_attack = row.away_score * adjustment_factor * (
                home_strength / (minimum_strength - dynamism_variable)
            ) - adjustment_factor * row.away_score * (
                (maximum_strength + dynamism_variable) / away_strength
            )
            home_attack = min(home_attack, ADJUSTED_GOAL_CAP)
            away_attack = min(away_attack, ADJUSTED_GOAL_CAP)
            attack[home] += max(home_attack, MINIMUM_OFFENSIVE_REWARD)
            defense[home] += max(away_attack, MINIMUM_OFFENSIVE_REWARD)
            attack[away] += max(away_attack, MINIMUM_OFFENSIVE_REWARD)
            defense[away] += max(home_attack, MINIMUM_OFFENSIVE_REWARD)
            continue

        home_attack = row.home_score * adjustment_factor * (
            away_strength / (minimum_strength - dynamism_variable)
            - (maximum_strength + dynamism_variable) / cutoff_strength
        )
        away_attack = row.away_score * adjustment_factor * (
            home_strength / (minimum_strength - dynamism_variable)
            - (maximum_strength + dynamism_variable) / cutoff_strength
        )
        home_defense = min(
            LOW_TEAM_DEFENSIVE_PENALTY_CAP,
            low_team_p_c * row.away_score * cutoff_strength / max(away_strength, 1e-9),
        )
        away_defense = min(
            LOW_TEAM_DEFENSIVE_PENALTY_CAP,
            low_team_p_c * row.home_score * cutoff_strength / max(home_strength, 1e-9),
        )
        attack[home] += min(ADJUSTED_GOAL_CAP, max(MINIMUM_OFFENSIVE_REWARD, home_attack))
        attack[away] += min(ADJUSTED_GOAL_CAP, max(MINIMUM_OFFENSIVE_REWARD, away_attack))
        if diagnostic_low_defense_floor:
            defense[home] += max(home_defense, MINIMUM_OFFENSIVE_REWARD)
            defense[away] += max(away_defense, MINIMUM_OFFENSIVE_REWARD)
        else:
            defense[home] += home_defense
            defense[away] += away_defense

    matches_played = weighted_matches["home_team"].value_counts().add(
        weighted_matches["away_team"].value_counts(), fill_value=0
    )
    rows = []
    for team in prior["team"]:
        count = float(matches_played.get(team, 0))
        if count <= 0:
            continue
        rows.append(
            {
                "team": team,
                "xG": attack[team] / count,
                "xGA": defense[team] / count,
                "matches": count,
            }
        )
    return pd.DataFrame(rows), float(low_team_p_c)


def calibrate_low_team_cutoff(
    matches: pd.DataFrame,
    prior: pd.DataFrame,
    quantiles: tuple[float, ...] = tuple(i / 100 for i in range(1, 26)),
    fallback_quantile: float = 0.07,
) -> tuple[float, pd.DataFrame]:
    eligible = _eligible_matches(matches, prior)
    if eligible.empty:
        raise ValueError("Cannot calibrate the low-team cutoff without eligible matches.")
    weighted = apply_goal_weights(eligible)
    base = estimate_stage_metric_parameters(
        stage_name="stage2",
        metric_series=prior["strength"],
        cutoff_quantile=quantiles[0],
    )
    trials = []
    for quantile in quantiles:
        cutoff = float(prior["strength"].quantile(quantile))
        metrics, low_team_p_c = _score_adjusted_metrics(
            weighted,
            prior,
            cutoff,
            float(base["adjustment_factor"]),
            float(base["dynamism_variable"]),
            diagnostic_low_defense_floor=True,
        )
        median_xg = float(metrics["xG"].median())
        median_xga = float(metrics["xGA"].median())
        median_goals = float(
            pd.concat([weighted["home_score"], weighted["away_score"]]).median()
        )
        if median_xg <= 0 or median_xga <= 0:
            raise ValueError("Low-team cutoff calibration produced a zero median metric.")
        scaled_xg = metrics["xG"] / median_xg * median_goals
        scaled_xga = metrics["xGA"] / median_xga * median_goals
        offending = metrics.loc[(scaled_xg < 1) & (scaled_xga < 1), "team"].tolist()
        trials.append(
            {
                "cutoff_quantile": quantile,
                "cutoff_strength": cutoff,
                "low_team_p_c": low_team_p_c,
                "observed_teams": len(metrics),
                "teams_below_one_on_both": len(offending),
                "offending_teams": "|".join(offending),
            }
        )
        if not offending:
            return quantile, pd.DataFrame(trials)
    trial_frame = pd.DataFrame(trials)
    trial_frame["selection_rule"] = "previous_cutoff_retained_no_diagnostic_solution"
    if fallback_quantile not in set(trial_frame["cutoff_quantile"]):
        raise ValueError("Fallback cutoff is not present in the calibration grid.")
    return float(fallback_quantile), trial_frame


def calculate_ratings(
    matches: pd.DataFrame,
    prior: pd.DataFrame,
    confederations: pd.DataFrame,
    cutoff_quantile: float,
) -> RatingRun:
    eligible = _eligible_matches(matches, prior)
    parameters = estimate_stage_metric_parameters(
        stage_name="stage2",
        metric_series=prior["strength"],
        cutoff_quantile=cutoff_quantile,
    )
    if eligible.empty:
        ratings = prior[["team", "off", "def", "confed"]].rename(
            columns={"off": "xG", "def": "xGA"}
        ).copy()
        ratings["matches"] = 0.0
        calibration = {
            "prior_team_count": int(len(prior)),
            "observed_team_count": 0,
            "rated_team_count_including_prior_carry_forward": int(len(ratings)),
            "prior_carry_forward_team_count": int(len(ratings)),
            "source_match_count": 0,
            "eligible_match_count": 0,
            "strength_lower": DEFAULT_STAGE2_STRENGTH_LOWER,
            "strength_upper": DEFAULT_STAGE2_STRENGTH_UPPER,
            "strength_minimum": float(parameters["minimum"]),
            "strength_maximum": float(parameters["maximum"]),
            "strength_median": float(parameters["median"]),
            "cutoff_quantile": float(cutoff_quantile),
            "cutoff_strength": float(parameters["cutoff_value"]),
            "adjustment_factor": float(parameters["adjustment_factor"]),
            "dynamism_variable": float(parameters["dynamism_variable"]),
            "friendly_goal_weight": FRIENDLY_WEIGHT,
        }
        return RatingRun(ratings, pd.DataFrame(columns=["team", "average_opponent_strength", "median_opponent_strength"]), calibration, eligible)
    weighted = apply_goal_weights(eligible)
    parameters = estimate_stage_metric_parameters(
        stage_name="stage2",
        metric_series=prior["strength"],
        cutoff_quantile=cutoff_quantile,
    )
    metrics, low_team_p_c = _score_adjusted_metrics(
        weighted,
        prior,
        float(parameters["cutoff_value"]),
        float(parameters["adjustment_factor"]),
        float(parameters["dynamism_variable"]),
        diagnostic_low_defense_floor=False,
    )

    strengths = prior.set_index("team")["strength"]
    average_opponents: dict[str, float] = {}
    median_opponents: dict[str, float] = {}
    for team in metrics["team"]:
        home = eligible[eligible["home_team"] == team]
        away = eligible[eligible["away_team"] == team]
        opponent_values = pd.concat(
            [home["away_team"].map(strengths), away["home_team"].map(strengths)],
            ignore_index=True,
        )
        if opponent_values.empty or opponent_values.isna().any():
            raise ValueError(f"Missing opponent strength for {team}.")
        average_opponents[team] = float(opponent_values.mean())
        median_opponents[team] = float(opponent_values.median())

    global_mean = float(prior["strength"].mean())
    global_median = float(prior["strength"].median())
    metrics["average_opponent_strength"] = metrics["team"].map(average_opponents)
    metrics["median_opponent_strength"] = metrics["team"].map(median_opponents)
    metrics["xG"] *= metrics["average_opponent_strength"] / global_mean
    metrics["xGA"] *= global_median / metrics["average_opponent_strength"]

    xga_95 = float(metrics["xGA"].quantile(0.95))
    metrics["xGA"] = metrics["xGA"].clip(lower=0, upper=xga_95)
    median_xg = float(metrics["xG"].median())
    median_xga = float(metrics["xGA"].median())
    complete_source_matches = matches.dropna(subset=["home_score", "away_score"])
    median_goals = float(
        pd.concat(
            [complete_source_matches["home_score"], complete_source_matches["away_score"]]
        ).median()
    )
    if median_xg <= 0 or median_xga <= 0:
        raise ValueError("Rating calculation produced a zero median metric.")
    metrics["xG"] = metrics["xG"] / median_xg * median_goals
    metrics["xGA"] = metrics["xGA"] / median_xga * median_goals

    missing_confeds = sorted(set(metrics["team"]).difference(confederations["team"]))
    if missing_confeds:
        raise ValueError(f"Missing confederations for: {missing_confeds}")
    ratings = metrics[["team", "xG", "xGA", "matches"]].merge(
        confederations, on="team", how="left", validate="one_to_one"
    )
    # Preserve prior ratings for teams with no observations in this phase. The
    # existing scripts implicitly dropped these teams; carrying them forward is
    # required for an empty/new-sample check and prevents name-valid countries
    # from disappearing merely because they had no fixture in the window.
    observed = set(ratings["team"])
    carry = prior.loc[~prior["team"].isin(observed), ["team", "off", "def"]].rename(
        columns={"off": "xG", "def": "xGA"}
    )
    # Re-express unobserved teams on this run's calibrated scale. Their
    # relative prior position is preserved, but the phase-wide median-goal
    # normalisation is applied rather than copying old absolute values.
    prior_off_median = float(prior["off"].median())
    prior_def_median = float(prior["def"].median())
    if prior_off_median <= 0 or prior_def_median <= 0:
        raise ValueError("Prior rating medians must be positive for carry-forward scaling.")
    carry["xG"] = carry["xG"] / prior_off_median * median_goals
    carry["xGA"] = carry["xGA"] / prior_def_median * median_goals
    carry["matches"] = 0.0
    carry = carry.merge(confederations, on="team", how="left", validate="one_to_one")
    ratings = pd.concat([ratings, carry], ignore_index=True)
    if not np.isfinite(ratings[["xG", "xGA", "matches"]].to_numpy()).all():
        raise ValueError("Non-finite values were produced in the ratings.")

    opponents = metrics[
        ["team", "average_opponent_strength", "median_opponent_strength"]
    ].copy()
    calibration = {
        "prior_team_count": int(len(prior)),
        "observed_team_count": int(len(metrics)),
        "rated_team_count_including_prior_carry_forward": int(len(ratings)),
        "prior_carry_forward_team_count": int(len(carry)),
        "source_match_count": int(len(complete_source_matches)),
        "eligible_match_count": int(len(eligible)),
        "friendly_match_count": int(eligible["tournament"].eq("Friendly").sum()),
        "strength_lower": DEFAULT_STAGE2_STRENGTH_LOWER,
        "strength_upper": DEFAULT_STAGE2_STRENGTH_UPPER,
        "strength_minimum": float(parameters["minimum"]),
        "strength_maximum": float(parameters["maximum"]),
        "strength_median": float(parameters["median"]),
        "cutoff_quantile": float(cutoff_quantile),
        "cutoff_strength": float(parameters["cutoff_value"]),
        "adjustment_factor": float(parameters["adjustment_factor"]),
        "dynamism_variable": float(parameters["dynamism_variable"]),
        "low_team_defensive_p_c": low_team_p_c,
        "global_mean_opponent_strength": global_mean,
        "global_median_opponent_strength": global_median,
        "corrected_xga_95th_percentile": xga_95,
        "corrected_xg_median_before_scaling": median_xg,
        "clipped_xga_median_before_scaling": median_xga,
        "raw_goal_median_for_scaling": median_goals,
        "friendly_goal_weight": FRIENDLY_WEIGHT,
        "max_goal_calibration_target": DEFAULT_MAX_GOAL_LIMIT,
        "adjusted_goal_cap": ADJUSTED_GOAL_CAP,
        "low_team_defensive_penalty_cap": LOW_TEAM_DEFENSIVE_PENALTY_CAP,
        "minimum_offensive_reward": MINIMUM_OFFENSIVE_REWARD,
    }
    return RatingRun(ratings, opponents, calibration, eligible)


def simulate_spi(
    ratings: pd.DataFrame,
    dictionary: pd.DataFrame,
    *,
    n_simulations: int = 10_000,
    seed: int | None = None,
) -> pd.DataFrame:
    if n_simulations <= 0:
        raise ValueError("n_simulations must be positive.")
    if seed is not None:
        np.random.seed(seed)
    ordered = pd.concat(
        [ratings[ratings["confed"] == confed] for confed in CONFEDERATION_ORDER],
        ignore_index=True,
    )
    ordered = ordered[ordered["team"] != "Russia"].reset_index(drop=True)
    if ordered["team"].duplicated().any():
        raise ValueError("Duplicate teams reached the simulation.")

    results = {team: {"wins": 0, "draws": 0, "losses": 0} for team in ordered["team"]}
    for index_a, team_a in ordered.iterrows():
        for index_b, team_b in ordered.iterrows():
            if index_a == index_b:
                continue
            lambda_a = (team_a["xG"] + team_b["xGA"]) / 2
            lambda_b = (team_b["xG"] + team_a["xGA"]) / 2
            goals_a = np.random.poisson(lambda_a, size=n_simulations)
            goals_b = np.random.poisson(lambda_b, size=n_simulations)
            wins_a = int(np.sum(goals_a > goals_b))
            draws = int(np.sum(goals_a == goals_b))
            wins_b = int(np.sum(goals_a < goals_b))
            results[team_a["team"]]["wins"] += wins_a
            results[team_a["team"]]["draws"] += draws
            results[team_a["team"]]["losses"] += wins_b
            results[team_b["team"]]["wins"] += wins_b
            results[team_b["team"]]["draws"] += draws
            results[team_b["team"]]["losses"] += wins_a

    total_matches = 2 * (len(ordered) - 1) * n_simulations
    if total_matches <= 0:
        raise ValueError("At least two rated teams are required for simulation.")
    spi_rows = []
    for team, result in results.items():
        points = result["wins"] * 3 + result["draws"]
        spi_rows.append({"team": team, "spi": points / total_matches / 3 * 100})
    output = ordered.merge(pd.DataFrame(spi_rows), on="team", validate="one_to_one")
    output["off"] = output["xG"]
    output["def"] = output["xGA"]
    original_to_corrected, _ = name_maps(dictionary)
    output["name"] = output["team"].map(original_to_corrected).fillna(output["team"])
    if output["name"].duplicated().any():
        duplicates = output.loc[output["name"].duplicated(False), "name"].tolist()
        raise ValueError(f"Display names collide after export mapping: {duplicates}")
    output["rank"] = output["spi"].rank(method="first", ascending=False).astype(int)
    return output[["rank", "name", "confed", "off", "def", "spi"]].sort_values(
        ["spi", "name"], ascending=[False, True]
    )


def compare_rankings(prior: pd.DataFrame, ranking: pd.DataFrame) -> pd.DataFrame:
    previous = prior[["rank", "name", "off", "def", "spi"]].rename(
        columns={
            "rank": "prior_rank",
            "off": "prior_off",
            "def": "prior_def",
            "spi": "prior_spi",
        }
    )
    current = ranking[["rank", "name", "off", "def", "spi"]].rename(
        columns={
            "rank": "new_rank",
            "off": "new_off",
            "def": "new_def",
            "spi": "new_spi",
        }
    )
    comparison = previous.merge(current, on="name", how="outer", validate="one_to_one")
    comparison["rank_change"] = comparison["prior_rank"] - comparison["new_rank"]
    comparison["off_change"] = comparison["new_off"] - comparison["prior_off"]
    comparison["def_change"] = comparison["new_def"] - comparison["prior_def"]
    comparison["spi_change"] = comparison["new_spi"] - comparison["prior_spi"]
    comparison["status"] = np.select(
        [comparison["prior_rank"].isna(), comparison["new_rank"].isna()],
        ["new_team", "not_rated_in_new_sample"],
        default="rated",
    )
    return comparison.sort_values(["new_rank", "prior_rank"], na_position="last")
