import pandas as pd
import numpy as np
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.paths import DICTIONARY_FILE, RESULTS_URL, STAGE2_PRIOR_FILE

PRIOR_FILE = STAGE2_PRIOR_FILE

# Load files
dictionary_df = pd.read_csv(DICTIONARY_FILE)
spi_rankings_df = pd.read_csv(PRIOR_FILE)
historical_data = pd.read_csv(RESULTS_URL)

# Correct team names in historical data using the dictionary
name_mapping = pd.Series(dictionary_df.corrected.values, index=dictionary_df.original).to_dict()
historical_data['home_team_corrected'] = historical_data['home_team'].map(name_mapping).fillna(historical_data['home_team'])
historical_data['away_team_corrected'] = historical_data['away_team'].map(name_mapping).fillna(historical_data['away_team'])

# Merge historical data with SPI rankings to get team identities aligned
merged_home = historical_data.merge(spi_rankings_df, left_on='home_team_corrected', right_on='name', suffixes=('', '_home'))
merged_away = historical_data.merge(spi_rankings_df, left_on='away_team_corrected', right_on='name', suffixes=('', '_away'))

# Top, median, and average teams from the prior table
top_teams = spi_rankings_df.sort_values(by='spi', ascending=False).head(20)['name']
median_team = spi_rankings_df.iloc[len(spi_rankings_df) // 2]['name']

average_spi = spi_rankings_df['spi'].mean()
average_team = spi_rankings_df.loc[(spi_rankings_df['spi'] - average_spi).abs().idxmin(), 'name']

# cap_off: average goals by top teams against median and average teams
top_scores_home_median = merged_home[
    merged_home['home_team_corrected'].isin(top_teams) &
    (merged_home['away_team_corrected'] == median_team)
]['home_score'].dropna().tolist()

top_scores_away_median = merged_away[
    merged_away['away_team_corrected'].isin(top_teams) &
    (merged_away['home_team_corrected'] == median_team)
]['away_score'].dropna().tolist()

top_scores_median = top_scores_home_median + top_scores_away_median

top_scores_home_avg = merged_home[
    merged_home['home_team_corrected'].isin(top_teams) &
    (merged_home['away_team_corrected'] == average_team)
]['home_score'].dropna().tolist()

top_scores_away_avg = merged_away[
    merged_away['away_team_corrected'].isin(top_teams) &
    (merged_away['home_team_corrected'] == average_team)
]['away_score'].dropna().tolist()

top_scores_avg = top_scores_home_avg + top_scores_away_avg

cap_off_median = np.mean(top_scores_median) if top_scores_median else np.nan
cap_off_avg = np.mean(top_scores_avg) if top_scores_avg else np.nan
cap_off = np.nanmean([cap_off_median, cap_off_avg])

# cap_def: average goals conceded by the very lowest group against a team near the 1st percentile
percentile_1_spi = spi_rankings_df['spi'].quantile(0.01)
percentile_1_team = spi_rankings_df.loc[(spi_rankings_df['spi'] - percentile_1_spi).abs().idxmin(), 'name']

low_teams_range = 5
median_index = len(spi_rankings_df) // 2
low_teams = spi_rankings_df.sort_values(by='spi', ascending=True).iloc[0:low_teams_range]['name']

def calculate_cap_def(low_teams, percentile_1_team):
    low_scores_home = merged_home[
        (merged_home['home_team_corrected'].isin(low_teams)) &
        (merged_home['away_team_corrected'] == percentile_1_team)
    ]['away_score'].dropna().tolist()

    low_scores_away = merged_away[
        (merged_away['away_team_corrected'].isin(low_teams)) &
        (merged_away['home_team_corrected'] == percentile_1_team)
    ]['home_score'].dropna().tolist()

    low_scores = low_scores_home + low_scores_away
    return np.mean(low_scores) if low_scores else np.nan, low_scores

cap_def, low_scores = calculate_cap_def(low_teams, percentile_1_team)

while (np.isnan(cap_def) or len(low_scores) < 5) and low_teams_range <= median_index:
    low_teams_range += 5
    low_teams = spi_rankings_df.sort_values(by='spi', ascending=True).iloc[0:low_teams_range]['name']
    cap_def, low_scores = calculate_cap_def(low_teams, percentile_1_team)

print("cap_off:", cap_off, "cap_def:", cap_def)
