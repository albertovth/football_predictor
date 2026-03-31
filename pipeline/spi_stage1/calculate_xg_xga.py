import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.paths import (
    AGGREGATED_XG_FILE,
    CONFEDERATIONS_FILE,
    CONFED_FILES,
    DICTIONARY_FILE,
    OPPONENT_SPI_FILE,
    RESULTS_URL,
    SPI_FINAL_FILE,
)


def report_saved_csv(path: str, df: pd.DataFrame) -> None:
    print(f"Saved: {path}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(df.head())
    print("-" * 60)


# -----------------------------
# Load the match data
# -----------------------------
df = pd.read_csv(RESULTS_URL)

# -----------------------------
# Load the SPI prior
# -----------------------------
spi_df = pd.read_csv(SPI_FINAL_FILE)
spi_df = spi_df.rename(columns={'name': 'team'})

cutoff_quantile_low_teams = 0.07  # structural cutoff
adjustment_factor = 0.017  # calculated with adjustment_factor_calculate_and_dynamism_variable.py
dynamism_variable = 0.16   # calculated with adjustment_factor_calculate_and_dynamism_variable.py

# Calculate SPI summary stats
median_spi = spi_df['spi'].median()
cutoff_quantile_spi = spi_df['spi'].quantile(cutoff_quantile_low_teams)
minimum_spi = spi_df['spi'].min()
maximum_spi = spi_df['spi'].max()

automatic_low_def_penalty_at_cutoff = max(
    adjustment_factor * (
        (median_spi / (minimum_spi - dynamism_variable))
        - ((maximum_spi + dynamism_variable) / cutoff_quantile_spi)
    ),
    0.01,
)

print(f"Median SPI: {median_spi}")
print(f"Cutoff Quantile SPI: {cutoff_quantile_spi}")
print(f"Minimum SPI: {minimum_spi}")
print(f"Maximum SPI: {maximum_spi}")
print(f"Adjustment factor: {adjustment_factor}")
print(f"Dynamism variable: {dynamism_variable}")
print(f"Baseline low-team defensive penalty at cutoff: {automatic_low_def_penalty_at_cutoff}")

# -----------------------------
# Load confederations and dictionary
# -----------------------------
confed_df = pd.read_csv(CONFEDERATIONS_FILE)
confed_df.columns = ['team', 'confed']

dictionary_df = pd.read_csv(DICTIONARY_FILE)
corrected_to_original = pd.Series(dictionary_df['original'].values, index=dictionary_df['corrected']).to_dict()

# Canonicalize names everywhere to original-style names used by your pipeline
spi_df['team'] = spi_df['team'].map(corrected_to_original).fillna(spi_df['team'])
confed_df['team'] = confed_df['team'].map(corrected_to_original).fillna(confed_df['team'])
df['home_team'] = df['home_team'].map(corrected_to_original).fillna(df['home_team'])
df['away_team'] = df['away_team'].map(corrected_to_original).fillna(df['away_team'])

# -----------------------------
# Filter stage 1 data window
# -----------------------------
start_date = pd.to_datetime('2021-05-26')
end_date = pd.to_datetime('2025-05-26')
df['date'] = pd.to_datetime(df['date'])
filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
filtered_df = filtered_df.dropna(subset=['home_score', 'away_score'])


def adjust_goals(row):
    if row['tournament'] == 'Friendly':
        return row['home_score'] * 0.5, row['away_score'] * 0.5
    return row['home_score'], row['away_score']


filtered_df[['home_score', 'away_score']] = filtered_df.apply(
    lambda row: pd.Series(adjust_goals(row)), axis=1
)

# Only include matches where both teams are in the SPI data
filtered_df = filtered_df[
    (filtered_df['home_team'].isin(spi_df['team'])) &
    (filtered_df['away_team'].isin(spi_df['team']))
].copy()

# -----------------------------
# Calculate match factors based on SPI
# -----------------------------
spi_factors = spi_df.set_index('team')['spi']

# Initialize points for xG and xGA
points_for_xG_high = {team: 0.0 for team in spi_df['team']}
points_for_xGA_high = {team: 0.0 for team in spi_df['team']}
points_for_xG_low = {team: 0.0 for team in spi_df['team']}
points_for_xGA_low = {team: 0.0 for team in spi_df['team']}

# High SPI teams
high_spi_teams = spi_df[spi_df['spi'] >= cutoff_quantile_spi]['team'].tolist()

# Low SPI teams
low_spi_teams = spi_df[spi_df['spi'] < cutoff_quantile_spi]['team'].tolist()


# -----------------------------
# Define the functions to calculate points
# -----------------------------
def calculate_points_high(row):
    home_team = row['home_team']
    away_team = row['away_team']

    if home_team not in spi_factors or away_team not in spi_factors:
        return

    spi_team1 = spi_factors.get(home_team, 1)
    spi_team2 = spi_factors.get(away_team, 1)

    adjusted_home_goals = (
        row['home_score'] * adjustment_factor * (spi_team2 / (minimum_spi - dynamism_variable))
        - adjustment_factor * row['home_score'] * ((maximum_spi + dynamism_variable) / spi_team1)
    )
    adjusted_away_goals = (
        row['away_score'] * adjustment_factor * (spi_team1 / (minimum_spi - dynamism_variable))
        - adjustment_factor * row['away_score'] * ((maximum_spi + dynamism_variable) / spi_team2)
    )

    # Cap points per match at 6
    adjusted_home_goals = min(adjusted_home_goals, 6)
    adjusted_away_goals = min(adjusted_away_goals, 6)

    points_for_xG_high[home_team] += max(adjusted_home_goals, 0.01)
    points_for_xGA_high[home_team] += max(adjusted_away_goals, 0.01)
    points_for_xG_high[away_team] += max(adjusted_away_goals, 0.01)
    points_for_xGA_high[away_team] += max(adjusted_home_goals, 0.01)


def calculate_points_low(row):
    """
    Balanced low-team regime in raw SPI space:
    - offensive reward depends on actual opponent SPI
    - own dampening is anchored at the cutoff SPI
    - defensive penalty is inferential and scales with how weak the scoring team is
    """
    home_team = row['home_team']
    away_team = row['away_team']

    if home_team not in spi_factors or away_team not in spi_factors:
        return

    spi_home = spi_factors.get(home_team, np.nan)
    spi_away = spi_factors.get(away_team, np.nan)

    # Low-team offensive reward:
    # actual opponent strength matters, own dampening anchored at cutoff
    home_off_reward = min(
        6,
        max(
            0.01,
            row['home_score'] * adjustment_factor * (
                (spi_away / (minimum_spi - dynamism_variable))
                - ((maximum_spi + dynamism_variable) / cutoff_quantile_spi)
            )
        )
    )

    away_off_reward = min(
        6,
        max(
            0.01,
            row['away_score'] * adjustment_factor * (
                (spi_home / (minimum_spi - dynamism_variable))
                - ((maximum_spi + dynamism_variable) / cutoff_quantile_spi)
            )
        )
    )

    # Low-team defensive penalty:
    # anchored at cutoff, harsher when conceding to weaker teams
    home_def_penalty = min(
        6,
        automatic_low_def_penalty_at_cutoff * row['away_score'] * (cutoff_quantile_spi / spi_away)
    )
    away_def_penalty = min(
        6,
        automatic_low_def_penalty_at_cutoff * row['home_score'] * (cutoff_quantile_spi / spi_home)
    )

    points_for_xG_low[home_team] += max(home_off_reward, 0.01)
    points_for_xGA_low[home_team] += max(home_def_penalty, 0.01)
    points_for_xG_low[away_team] += max(away_off_reward, 0.01)
    points_for_xGA_low[away_team] += max(away_def_penalty, 0.01)


# Apply the functions to calculate points
filtered_df.apply(
    lambda row: calculate_points_high(row)
    if row['home_team'] in high_spi_teams and row['away_team'] in high_spi_teams
    else calculate_points_low(row),
    axis=1
)

# Combine the points
points_for_xG = {team: points_for_xG_high[team] + points_for_xG_low[team] for team in spi_df['team']}
points_for_xGA = {team: points_for_xGA_high[team] + points_for_xGA_low[team] for team in spi_df['team']}

# Calculate matches played
matches_played = filtered_df['home_team'].value_counts().add(
    filtered_df['away_team'].value_counts(),
    fill_value=0
).to_dict()

# Calculate xG and xGA
xg_data = []
for team in points_for_xG.keys():
    matches = matches_played.get(team, 1)  # Default to 1 to avoid division by zero
    xg = points_for_xG[team] / matches
    xga = points_for_xGA[team] / matches
    xg_data.append({'team': team, 'xG': xg, 'xGA': xga, 'matches': matches})

xg_df = pd.DataFrame(xg_data)
print("Initial xg_df:")
print(xg_df.head())
print(xg_df.shape)
print("-" * 60)

# Calculate correction factors based on average and median opponent SPI
average_opponent_spi = {team: 0 for team in spi_df['team']}
median_opponent_spi = {team: [] for team in spi_df['team']}
for team in spi_df['team']:
    home_matches = filtered_df[filtered_df['home_team'] == team]
    away_matches = filtered_df[filtered_df['away_team'] == team]
    opponent_spi_sum = home_matches['away_team'].map(spi_factors).sum() + away_matches['home_team'].map(spi_factors).sum()
    opponent_spi_values = home_matches['away_team'].map(spi_factors).tolist() + away_matches['home_team'].map(spi_factors).tolist()
    total_matches = len(home_matches) + len(away_matches)
    average_opponent_spi[team] = opponent_spi_sum / total_matches if total_matches > 0 else median_spi
    median_opponent_spi[team] = pd.Series(opponent_spi_values).median() if opponent_spi_values else median_spi

# Calculate global mean and median SPI
global_mean_spi = spi_df['spi'].mean()
global_median_spi = spi_df['spi'].median()

# Apply correction factors
for team in xg_df['team']:
    avg_spi = average_opponent_spi[team]
    med_spi = median_opponent_spi[team]
    offense_correction = avg_spi / global_mean_spi
    defense_correction = global_median_spi / avg_spi
    xg_df.loc[xg_df['team'] == team, 'xG'] *= offense_correction
    xg_df.loc[xg_df['team'] == team, 'xGA'] *= defense_correction

percentile_95th_xGA_corrected = xg_df['xGA'].quantile(0.95)
print(f"95th Percentile for Corrected xGA: {percentile_95th_xGA_corrected}")

xg_df['xGA'] = xg_df['xGA'].clip(lower=0, upper=percentile_95th_xGA_corrected)

# Check for NaN values in average and median opponent SPI
nan_teams = {
    team: (avg_spi, med_spi)
    for team, avg_spi, med_spi in zip(
        average_opponent_spi.keys(),
        average_opponent_spi.values(),
        median_opponent_spi.values()
    )
    if pd.isna(avg_spi) or pd.isna(med_spi)
}

print("Teams with NaN values in average or median opponent SPI:")
for team, (avg_spi, med_spi) in nan_teams.items():
    print(f"{team}: Average SPI={avg_spi}, Median SPI={med_spi}")
print("-" * 60)

# Save average and median opponent SPI to a new CSV file
opponent_spi_data = [
    {'team': team, 'average_opponent_spi': avg_spi, 'median_opponent_spi': med_spi}
    for team, avg_spi, med_spi in zip(
        average_opponent_spi.keys(),
        average_opponent_spi.values(),
        median_opponent_spi.values()
    )
]
opponent_spi_df = pd.DataFrame(opponent_spi_data)
OPPONENT_SPI_FILE.parent.mkdir(parents=True, exist_ok=True)
opponent_spi_path = OPPONENT_SPI_FILE
opponent_spi_df.to_csv(opponent_spi_path, index=False)
report_saved_csv(opponent_spi_path, opponent_spi_df)

# Compute medians for adjustment
median_xG = xg_df['xG'].median()
median_xGA = xg_df['xGA'].median()

# Load historical data for rescaling
historical_data = pd.read_csv(RESULTS_URL)
historical_data['date'] = pd.to_datetime(historical_data['date'])
filtered_data = historical_data[(historical_data['date'] >= start_date) & (historical_data['date'] <= end_date)].copy()

all_goals = pd.concat([filtered_data['home_score'], filtered_data['away_score']])
median_goals_per_team = all_goals.median()
print(f"Median goals per team in stage 1 window: {median_goals_per_team}")

# Apply the multiplicative adjustment
xg_df['xG'] = (xg_df['xG'] / median_xG) * median_goals_per_team
xg_df['xGA'] = (xg_df['xGA'] / median_xGA) * median_goals_per_team

# Merge with confederations data to filter out only the relevant teams
xg_df = xg_df.merge(confed_df, on='team', how='inner')

# Save the aggregated data to a new CSV file
aggregated_path = AGGREGATED_XG_FILE
xg_df.to_csv(aggregated_path, index=False)
report_saved_csv(aggregated_path, xg_df)

# Separate and save data for each confederation, without the 'confed' column
conmebol_teams = xg_df[xg_df['confed'] == 'CONMEBOL'].drop(columns=['confed'])
uefa_teams = xg_df[xg_df['confed'] == 'UEFA'].drop(columns=['confed'])
concacaf_teams = xg_df[xg_df['confed'] == 'CONCACAF'].drop(columns=['confed'])
afc_teams = xg_df[xg_df['confed'] == 'AFC'].drop(columns=['confed'])
caf_teams = xg_df[xg_df['confed'] == 'CAF'].drop(columns=['confed'])
ofc_teams = xg_df[xg_df['confed'] == 'OFC'].drop(columns=['confed'])

conmebol_path = CONFED_FILES['CONMEBOL']
uefa_path = CONFED_FILES['UEFA']
concacaf_path = CONFED_FILES['CONCACAF']
afc_path = CONFED_FILES['AFC']
caf_path = CONFED_FILES['CAF']
ofc_path = CONFED_FILES['OFC']

conmebol_teams.to_csv(conmebol_path, index=False)
uefa_teams.to_csv(uefa_path, index=False)
concacaf_teams.to_csv(concacaf_path, index=False)
afc_teams.to_csv(afc_path, index=False)
caf_teams.to_csv(caf_path, index=False)
ofc_teams.to_csv(ofc_path, index=False)

report_saved_csv(conmebol_path, conmebol_teams)
report_saved_csv(uefa_path, uefa_teams)
report_saved_csv(concacaf_path, concacaf_teams)
report_saved_csv(afc_path, afc_teams)
report_saved_csv(caf_path, caf_teams)
report_saved_csv(ofc_path, ofc_teams)
