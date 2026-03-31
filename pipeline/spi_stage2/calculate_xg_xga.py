
import pandas as pd
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
    OPPONENT_STRENGTH_FILE,
    RESULTS_URL,
    SPI_FINAL_FILE,
)

def add_strength(df, spi_col="spi", lower=0.05, upper=0.95):
    df = df.copy()
    n = len(df)
    if n <= 1:
        df["strength"] = 0.5
        return df
    ranks = df[spi_col].rank(method="average")
    pct = (ranks - 1) / (n - 1)
    df["strength"] = lower + (upper - lower) * pct
    return df

# Load the match data
df = pd.read_csv(RESULTS_URL)

# Load the SPI data
spi_df = pd.read_csv(SPI_FINAL_FILE)
spi_df = spi_df.rename(columns={'name': 'team'})
spi_df = add_strength(spi_df, spi_col="spi", lower=0.05, upper=0.95)

cutoff_quantile_low_teams = 0.07

# Summary statistics on internal strength scale
median_strength = spi_df['strength'].median()
cutoff_quantile_strength = spi_df['strength'].quantile(cutoff_quantile_low_teams)
minimum_strength = spi_df['strength'].min()
maximum_strength = spi_df['strength'].max()

print(f"Median strength: {median_strength}")
print(f"Cutoff quantile strength: {cutoff_quantile_strength}")
print(f"Minimum strength: {minimum_strength}")
print(f"Maximum strength: {maximum_strength}")

# Load dictionary and confederations
dictionary_df = pd.read_csv(DICTIONARY_FILE)
corrected_to_original = pd.Series(dictionary_df['original'].values, index=dictionary_df['corrected']).to_dict()

confed_df = pd.read_csv(CONFEDERATIONS_FILE)
confed_df.columns = ['team', 'confed']
# Canonicalize confederation names to the same namespace used in computation
confed_df['team'] = confed_df['team'].map(corrected_to_original).fillna(confed_df['team'])
confed_df = confed_df.drop_duplicates(subset=['team']).copy()

# Canonicalize team names in SPI and match data
spi_df['team'] = spi_df['team'].map(corrected_to_original).fillna(spi_df['team'])
df['home_team'] = df['home_team'].map(corrected_to_original).fillna(df['home_team'])
df['away_team'] = df['away_team'].map(corrected_to_original).fillna(df['away_team'])

# Filter date window
today = datetime.today()
start_date = pd.to_datetime('2025-05-27')
df['date'] = pd.to_datetime(df['date'])
filtered_df = df[(df['date'] >= start_date) & (df['date'] <= today)]
filtered_df = filtered_df.dropna(subset=['home_score', 'away_score'])

def adjust_goals(row):
    if row['tournament'] == 'Friendly':
        return row['home_score'] * 0.5, row['away_score'] * 0.5
    return row['home_score'], row['away_score']

filtered_df[['home_score', 'away_score']] = filtered_df.apply(
    lambda row: pd.Series(adjust_goals(row)), axis=1
)

# Keep only teams in the stage-2 prior universe
filtered_df = filtered_df[
    (filtered_df['home_team'].isin(spi_df['team'])) &
    (filtered_df['away_team'].isin(spi_df['team']))
]

strength_factors = spi_df.set_index('team')['strength']

points_for_xG_high = {team: 0 for team in spi_df['team']}
points_for_xGA_high = {team: 0 for team in spi_df['team']}
points_for_xG_low = {team: 0 for team in spi_df['team']}
points_for_xGA_low = {team: 0 for team in spi_df['team']}

high_strength_teams = spi_df[spi_df['strength'] >= cutoff_quantile_strength]['team'].tolist()

ADJUSTMENT_FACTOR = 0.333
DYNAMISM_VARIABLE = 0.025
LOW_TEAM_DEFENSIVE_PENALTY_CAP = 6
LOW_TEAM_MIN_OFFENSIVE_REWARD = 0.01

# Inferential low-team defensive anchor at the cutoff: one goal conceded
# to a team exactly at the cutoff should imply a severe but not automatic-max
# defensive penalty, and weaker scoring teams imply a larger penalty.
LOW_TEAM_DEFENSIVE_P_C = max(
    ADJUSTMENT_FACTOR * (
        (median_strength / (minimum_strength - DYNAMISM_VARIABLE))
        - ((maximum_strength + DYNAMISM_VARIABLE) / cutoff_quantile_strength)
    ),
    0.01
)

print(f"Low-team defensive P_c: {LOW_TEAM_DEFENSIVE_P_C}")

def calculate_points_high(row, maximum_strength, minimum_strength):
    home_team = row['home_team']
    away_team = row['away_team']

    if home_team not in strength_factors or away_team not in strength_factors:
        return

    strength_team1 = strength_factors.get(home_team, 0.5)
    strength_team2 = strength_factors.get(away_team, 0.5)

    adjusted_home_goals = (
        row['home_score'] * ADJUSTMENT_FACTOR * (strength_team2 / (minimum_strength - DYNAMISM_VARIABLE))
        - ADJUSTMENT_FACTOR * row['home_score'] * ((maximum_strength + DYNAMISM_VARIABLE) / strength_team1)
    )
    adjusted_away_goals = (
        row['away_score'] * ADJUSTMENT_FACTOR * (strength_team1 / (minimum_strength - DYNAMISM_VARIABLE))
        - ADJUSTMENT_FACTOR * row['away_score'] * ((maximum_strength + DYNAMISM_VARIABLE) / strength_team2)
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

    if home_team not in points_for_xG_low or away_team not in points_for_xG_low:
        return

    home_team_strength = strength_factors.get(home_team, cutoff_quantile_strength)
    away_team_strength = strength_factors.get(away_team, cutoff_quantile_strength)

    # Inferential low-team offense rule:
    # keep the opponent's actual strength in the reward term,
    # but anchor the scoring team's dampening term at the cutoff strength
    # so low teams can be recognized for scoring against stronger teams
    # without exploding because of tiny own-strength values.
    adjusted_home_goals_low = row['home_score'] * ADJUSTMENT_FACTOR * (
        (away_team_strength / (minimum_strength - DYNAMISM_VARIABLE))
        - ((maximum_strength + DYNAMISM_VARIABLE) / cutoff_quantile_strength)
    )
    adjusted_away_goals_low = row['away_score'] * ADJUSTMENT_FACTOR * (
        (home_team_strength / (minimum_strength - DYNAMISM_VARIABLE))
        - ((maximum_strength + DYNAMISM_VARIABLE) / cutoff_quantile_strength)
    )

    adjusted_home_xga_low = min(
        LOW_TEAM_DEFENSIVE_PENALTY_CAP,
        LOW_TEAM_DEFENSIVE_P_C * row['away_score'] * (cutoff_quantile_strength / max(away_team_strength, 1e-9))
    )
    adjusted_away_xga_low = min(
        LOW_TEAM_DEFENSIVE_PENALTY_CAP,
        LOW_TEAM_DEFENSIVE_P_C * row['home_score'] * (cutoff_quantile_strength / max(home_team_strength, 1e-9))
    )

    points_for_xG_low[home_team] += min(6, max(LOW_TEAM_MIN_OFFENSIVE_REWARD, adjusted_home_goals_low))
    points_for_xGA_low[home_team] += adjusted_home_xga_low
    points_for_xG_low[away_team] += min(6, max(LOW_TEAM_MIN_OFFENSIVE_REWARD, adjusted_away_goals_low))
    points_for_xGA_low[away_team] += adjusted_away_xga_low

filtered_df.apply(
    lambda row: calculate_points_high(row, maximum_strength, minimum_strength)
    if row['home_team'] in high_strength_teams and row['away_team'] in high_strength_teams
    else calculate_points_low(row),
    axis=1
)

points_for_xG = {team: points_for_xG_high[team] + points_for_xG_low[team] for team in spi_df['team']}
points_for_xGA = {team: points_for_xGA_high[team] + points_for_xGA_low[team] for team in spi_df['team']}

matches_played = filtered_df['home_team'].value_counts().add(
    filtered_df['away_team'].value_counts(), fill_value=0
)
matches_played = matches_played.to_dict()

xg_data = []
for team in points_for_xG.keys():
    matches = matches_played.get(team, 0)
    if matches <= 0:
        continue
    xg = points_for_xG[team] / matches
    xga = points_for_xGA[team] / matches
    xg_data.append({'team': team, 'xG': xg, 'xGA': xga, 'matches': float(matches)})

xg_df = pd.DataFrame(xg_data)

average_opponent_strength = {}
median_opponent_strength = {}

for team in xg_df['team']:
    home_matches = filtered_df[filtered_df['home_team'] == team]
    away_matches = filtered_df[filtered_df['away_team'] == team]
    opponent_strength_sum = home_matches['away_team'].map(strength_factors).sum() + away_matches['home_team'].map(strength_factors).sum()
    opponent_strength_values = home_matches['away_team'].map(strength_factors).tolist() + away_matches['home_team'].map(strength_factors).tolist()
    total_matches = len(home_matches) + len(away_matches)
    average_opponent_strength[team] = opponent_strength_sum / total_matches if total_matches > 0 else median_strength
    median_opponent_strength[team] = pd.Series(opponent_strength_values).median() if opponent_strength_values else median_strength

global_mean_strength = spi_df['strength'].mean()
global_median_strength = spi_df['strength'].median()

for team in xg_df['team']:
    avg_strength = average_opponent_strength[team]
    offense_correction = avg_strength / global_mean_strength
    defense_correction = global_median_strength / avg_strength
    xg_df.loc[xg_df['team'] == team, 'xG'] *= offense_correction
    xg_df.loc[xg_df['team'] == team, 'xGA'] *= defense_correction

percentile_95th_xGA_corrected = xg_df['xGA'].quantile(0.95)
print(f"95th Percentile for Corrected xGA: {percentile_95th_xGA_corrected}")
xg_df['xGA'] = xg_df['xGA'].clip(lower=0, upper=percentile_95th_xGA_corrected)

opponent_strength_df = pd.DataFrame([
    {'team': team, 'average_opponent_strength': average_opponent_strength[team], 'median_opponent_strength': median_opponent_strength[team]}
    for team in xg_df['team']
])
OPPONENT_STRENGTH_FILE.parent.mkdir(parents=True, exist_ok=True)
opponent_strength_path = OPPONENT_STRENGTH_FILE
opponent_strength_df.to_csv(opponent_strength_path, index=False)

print(f"Saved: {opponent_strength_path}")
print(f"Shape: {opponent_strength_df.shape}")
print(f"Columns: {list(opponent_strength_df.columns)}")
print(opponent_strength_df.head())

median_xG = xg_df['xG'].median()
median_xGA = xg_df['xGA'].median()

historical_data = pd.read_csv(RESULTS_URL)
historical_data['date'] = pd.to_datetime(historical_data['date'])
filtered_data = historical_data[(historical_data['date'] >= start_date) & (historical_data['date'] <= today)]

all_goals = pd.concat([filtered_data['home_score'], filtered_data['away_score']])
median_goals_per_team = all_goals.median()

xg_df['xG'] = (xg_df['xG'] / median_xG) * median_goals_per_team
xg_df['xGA'] = (xg_df['xGA'] / median_xGA) * median_goals_per_team

# Inner merge after canonicalization; no blank rows should survive
xg_df = xg_df.merge(confed_df, on='team', how='inner')

# Final safety: drop any residual blanks
xg_df = xg_df.dropna(subset=['xG', 'xGA', 'matches', 'confed']).copy()

aggregated_path = AGGREGATED_XG_FILE
xg_df.to_csv(aggregated_path, index=False)
print(f"Saved: {aggregated_path}")
print(f"Shape: {xg_df.shape}")
print(f"Columns: {list(xg_df.columns)}")
print(xg_df.head())

confed_outputs = {
    CONFED_FILES['CONMEBOL']: xg_df[xg_df['confed'] == 'CONMEBOL'].drop(columns=['confed']),
    CONFED_FILES['UEFA']: xg_df[xg_df['confed'] == 'UEFA'].drop(columns=['confed']),
    CONFED_FILES['CONCACAF']: xg_df[xg_df['confed'] == 'CONCACAF'].drop(columns=['confed']),
    CONFED_FILES['AFC']: xg_df[xg_df['confed'] == 'AFC'].drop(columns=['confed']),
    CONFED_FILES['CAF']: xg_df[xg_df['confed'] == 'CAF'].drop(columns=['confed']),
    CONFED_FILES['OFC']: xg_df[xg_df['confed'] == 'OFC'].drop(columns=['confed']),
}

for path, out_df in confed_outputs.items():
    out_df = out_df.dropna(subset=['xG', 'xGA', 'matches']).copy()
    out_df.to_csv(path, index=False)
    print(f"Saved: {path}")
    print(f"Shape: {out_df.shape}")
    print(f"Columns: {list(out_df.columns)}")
    print(out_df.head())
