import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.paths import DICTIONARY_FILE, RESULTS_URL, SPI_FINAL_FILE

# -----------------------------
# Helpers
# -----------------------------
def add_strength(df, spi_col="spi", lower=0.05, upper=0.95):
    df = df.copy()
    n = len(df)
    if n == 1:
        df["strength"] = 0.5
        return df
    ranks = df[spi_col].rank(method="average")
    pct = (ranks - 1) / (n - 1)
    df["strength"] = lower + (upper - lower) * pct
    return df

# -----------------------------
# Load prior
# -----------------------------
spi_df = pd.read_csv(SPI_FINAL_FILE)
spi_df = spi_df.rename(columns={'name': 'team'})
spi_df = add_strength(spi_df, spi_col="spi", lower=0.05, upper=0.95)

# -----------------------------
# Load dictionary / canonicalize
# -----------------------------
dictionary_df = pd.read_csv(DICTIONARY_FILE)
corrected_to_original = pd.Series(
    dictionary_df['original'].values,
    index=dictionary_df['corrected']
).to_dict()

spi_df['team'] = spi_df['team'].map(corrected_to_original).fillna(spi_df['team'])

# -----------------------------
# Load and preprocess match data
# -----------------------------
df = pd.read_csv(RESULTS_URL)

df['home_team'] = df['home_team'].map(corrected_to_original).fillna(df['home_team'])
df['away_team'] = df['away_team'].map(corrected_to_original).fillna(df['away_team'])

spi_teams = spi_df['team'].tolist()
df = df[(df['home_team'].isin(spi_teams)) & (df['away_team'].isin(spi_teams))]

df['date'] = pd.to_datetime(df['date'])
start_date = pd.to_datetime('2025-05-27')
end_date = pd.to_datetime('2026-03-23')

filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
filtered_df = filtered_df.dropna(subset=['home_score', 'away_score'])

def adjust_goals(row):
    if row['tournament'] == 'Friendly':
        return row['home_score'] * 0.5, row['away_score'] * 0.5
    return row['home_score'], row['away_score']

filtered_df[['home_score', 'away_score']] = filtered_df.apply(
    lambda row: pd.Series(adjust_goals(row)), axis=1
)

# -----------------------------
# Constants from your corrected stage 2
# -----------------------------
adjustment_factor = 0.333
dynamism_variable = 0.025

strength_factors = spi_df.set_index('team')['strength']

quantile_range = [0.01 * i for i in range(1, 26)]

for cutoff_quantile_low_teams in quantile_range:
    median_strength = spi_df['strength'].median()
    cutoff_quantile_strength = spi_df['strength'].quantile(cutoff_quantile_low_teams)
    minimum_strength = spi_df['strength'].min()
    maximum_strength = spi_df['strength'].max()

    print(f"Testing with cutoff quantile: {cutoff_quantile_low_teams}")
    print(f"Cutoff Quantile strength: {cutoff_quantile_strength}")

    # Baseline low-team defensive penalty at the cutoff
    P_c = max(
        adjustment_factor * (
            (median_strength / (minimum_strength - dynamism_variable))
            - ((maximum_strength + dynamism_variable) / cutoff_quantile_strength)
        ),
        0.01
    )

    points_for_xG_high = {team: 0 for team in spi_df['team']}
    points_for_xGA_high = {team: 0 for team in spi_df['team']}
    points_for_xG_low = {team: 0 for team in spi_df['team']}
    points_for_xGA_low = {team: 0 for team in spi_df['team']}

    high_strength_teams = spi_df[spi_df['strength'] >= cutoff_quantile_strength]['team'].tolist()
    low_strength_teams = spi_df[spi_df['strength'] < cutoff_quantile_strength]['team'].tolist()

    def calculate_points_high(row):
        home_team = row['home_team']
        away_team = row['away_team']

        if home_team not in strength_factors or away_team not in strength_factors:
            return

        s1 = strength_factors.get(home_team, 1)
        s2 = strength_factors.get(away_team, 1)

        adjusted_home_goals = (
            row['home_score'] * adjustment_factor * (s2 / (minimum_strength - dynamism_variable))
            - adjustment_factor * row['home_score'] * ((maximum_strength + dynamism_variable) / s1)
        )
        adjusted_away_goals = (
            row['away_score'] * adjustment_factor * (s1 / (minimum_strength - dynamism_variable))
            - adjustment_factor * row['away_score'] * ((maximum_strength + dynamism_variable) / s2)
        )

        adjusted_home_goals = min(adjusted_home_goals, 6)
        adjusted_away_goals = min(adjusted_away_goals, 6)

        points_for_xG_high[home_team] += max(adjusted_home_goals, 0.01)
        points_for_xGA_high[home_team] += max(adjusted_away_goals, 0.01)
        points_for_xG_high[away_team] += max(adjusted_away_goals, 0.01)
        points_for_xGA_high[away_team] += max(adjusted_home_goals, 0.01)

    def calculate_points_low(row):
        home_team = row['home_team']
        away_team = row['away_team']

        if home_team not in strength_factors or away_team not in strength_factors:
            return

        s_home = strength_factors.get(home_team, np.nan)
        s_away = strength_factors.get(away_team, np.nan)

        # Low-team offensive reward:
        # actual opponent strength matters, own dampening anchored at cutoff
        home_off_reward = min(
            6,
            max(
                0.01,
                row['home_score'] * adjustment_factor * (
                    (s_away / (minimum_strength - dynamism_variable))
                    - ((maximum_strength + dynamism_variable) / cutoff_quantile_strength)
                )
            )
        )

        away_off_reward = min(
            6,
            max(
                0.01,
                row['away_score'] * adjustment_factor * (
                    (s_home / (minimum_strength - dynamism_variable))
                    - ((maximum_strength + dynamism_variable) / cutoff_quantile_strength)
                )
            )
        )

        # Low-team defensive penalty:
        # anchored at cutoff, harsher when conceding to weaker low teams
        home_def_penalty = min(
            6,
            P_c * row['away_score'] * (cutoff_quantile_strength / s_away)
        )
        away_def_penalty = min(
            6,
            P_c * row['home_score'] * (cutoff_quantile_strength / s_home)
        )

        points_for_xG_low[home_team] += max(home_off_reward, 0.01)
        points_for_xGA_low[home_team] += max(home_def_penalty, 0.01)
        points_for_xG_low[away_team] += max(away_off_reward, 0.01)
        points_for_xGA_low[away_team] += max(away_def_penalty, 0.01)

    filtered_df.apply(
        lambda row: calculate_points_high(row)
        if row['home_team'] in high_strength_teams and row['away_team'] in high_strength_teams
        else calculate_points_low(row),
        axis=1
    )

    points_for_xG = {
        team: points_for_xG_high[team] + points_for_xG_low[team]
        for team in spi_df['team']
    }
    points_for_xGA = {
        team: points_for_xGA_high[team] + points_for_xGA_low[team]
        for team in spi_df['team']
    }

    matches_played = filtered_df['home_team'].value_counts().add(
        filtered_df['away_team'].value_counts(),
        fill_value=0
    ).to_dict()

    xg_data = []
    for team in points_for_xG.keys():
        matches = matches_played.get(team, 1)
        xg = points_for_xG[team] / matches
        xga = points_for_xGA[team] / matches
        xg_data.append({'team': team, 'xG': xg, 'xGA': xga, 'matches': matches})

    xg_df = pd.DataFrame(xg_data)

    # Rescale to goal-like units, same logic as production
    median_xG = xg_df['xG'].median()
    median_xGA = xg_df['xGA'].median()

    all_goals = pd.concat([filtered_df['home_score'], filtered_df['away_score']])
    median_goals_per_team = all_goals.median()

    xg_df['xG'] = (xg_df['xG'] / median_xG) * median_goals_per_team
    xg_df['xGA'] = (xg_df['xGA'] / median_xGA) * median_goals_per_team

    low_xg_xga_teams = xg_df[(xg_df['xG'] < 1) & (xg_df['xGA'] < 1)]

    if low_xg_xga_teams.empty:
        print(f"Found a suitable quantile: {cutoff_quantile_low_teams}")
        break
    else:
        print(
            f"Teams with xG and xGA both under 1 at quantile {cutoff_quantile_low_teams}:\n"
            f"{low_xg_xga_teams.sort_values(['matches', 'team'])}"
        )

    print("-" * 50)
