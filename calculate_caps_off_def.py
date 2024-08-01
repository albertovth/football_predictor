import pandas as pd
import numpy as np

# Load the provided files
dictionary_df = pd.read_csv('/home/albertovth/SPI/dictionary.csv')
spi_rankings_df = pd.read_csv('/home/albertovth/SPI/spi_global_rankings_intl_25_5_2021.csv')

# Historical data (should be previously filtered to the recent matches)
historical_data = pd.read_csv('https://raw.githubusercontent.com/martj42/international_results/master/results.csv')

# Correct team names in historical data using the dictionary
name_mapping = pd.Series(dictionary_df.corrected.values, index=dictionary_df.original).to_dict()
historical_data['home_team_corrected'] = historical_data['home_team'].map(name_mapping).fillna(historical_data['home_team'])
historical_data['away_team_corrected'] = historical_data['away_team'].map(name_mapping).fillna(historical_data['away_team'])

# Merge historical data with SPI rankings to get Off and Def values
merged_home = historical_data.merge(spi_rankings_df, left_on='home_team_corrected', right_on='name', suffixes=('', '_home'))
merged_away = historical_data.merge(spi_rankings_df, left_on='away_team_corrected', right_on='name', suffixes=('', '_away'))

# Calculate the cap for Off (xG) as the average score scored by a top team to the median and average teams
top_teams = spi_rankings_df.sort_values(by='spi', ascending=False).head(20)['name']
median_team = spi_rankings_df.iloc[len(spi_rankings_df) // 2]['name']

average_spi = spi_rankings_df['spi'].mean()
average_team = spi_rankings_df.iloc[(spi_rankings_df['spi'] - average_spi).abs().idxmin()]['name']

top_scores_home_median = merged_home[merged_home['home_team_corrected'].isin(top_teams) & (merged_home['away_team_corrected'] == median_team)]['home_score'].dropna().tolist()
top_scores_away_median = merged_away[merged_away['away_team_corrected'].isin(top_teams) & (merged_away['home_team_corrected'] == median_team)]['away_score'].dropna().tolist()
top_scores_median = top_scores_home_median + top_scores_away_median

top_scores_home_avg = merged_home[merged_home['home_team_corrected'].isin(top_teams) & (merged_home['away_team_corrected'] == average_team)]['home_score'].dropna().tolist()
top_scores_away_avg = merged_away[merged_away['away_team_corrected'].isin(top_teams) & (merged_away['home_team_corrected'] == average_team)]['away_score'].dropna().tolist()
top_scores_avg = top_scores_home_avg + top_scores_away_avg

cap_off_median = np.mean(top_scores_median) if top_scores_median else np.nan
cap_off_avg = np.mean(top_scores_avg) if top_scores_avg else np.nan

# Combine the caps using a weighted average
cap_off = (cap_off_median + cap_off_avg) / 2

# Calculate the 25th percentile team
percentile_1_spi = spi_rankings_df['spi'].quantile(0.01)
percentile_1_team = spi_rankings_df[spi_rankings_df['spi'] >= percentile_1_spi].iloc[0]['name']

# Initialize variables to dynamically adjust the range of low teams
low_teams_range = 5
median_index = len(spi_rankings_df) // 2  # Index of the median team
low_teams = spi_rankings_df.sort_values(by='spi', ascending=True).iloc[0:low_teams_range]['name']




# Function to calculate cap_def
def calculate_cap_def(low_teams, percentile_1_team):
    low_scores_home = merged_home[(merged_home['home_team_corrected'].isin(low_teams)) & (merged_home['away_team_corrected'] == percentile_1_team)]['away_score'].dropna().tolist()
    low_scores_away = merged_away[(merged_away['away_team_corrected'].isin(low_teams)) & (merged_away['home_team_corrected'] == percentile_1_team)]['home_score'].dropna().tolist()
    low_scores = low_scores_home + low_scores_away
    return np.mean(low_scores) if low_scores else np.nan, low_scores

cap_def, low_scores = calculate_cap_def(low_teams, percentile_1_team)

# Dynamically adjust the range if cap_def is NaN or based on the number of matches
while (np.isnan(cap_def) or len(low_scores) < 5) and low_teams_range <= median_index:
    low_teams_range += 5
    low_teams = spi_rankings_df.sort_values(by='spi', ascending=True).iloc[0:low_teams_range]['name']
    cap_def, low_scores = calculate_cap_def(low_teams, percentile_1_team)

print("cap_off:", cap_off, "cap_def:", cap_def)

