import pandas as pd
from datetime import datetime, timedelta

# Load the match data
url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
df = pd.read_csv(url)

# Load the SPI data
spi_df = pd.read_csv('/home/albertovth/SPI/spi_final.csv')
spi_df = spi_df.rename(columns={'name': 'team'})

# Calculate the median SPI and 25th percentile SPI for the three confederations combined
median_spi = spi_df['spi'].median()
twenty_fifth_percentile_spi = spi_df['spi'].quantile(0.25)
print(f"Median SPI: {median_spi}")
print(f"25th Percentile SPI: {twenty_fifth_percentile_spi}")

# Load the confederations data
confed_df = pd.read_csv('/home/albertovth/SPI/confederations.csv')
confed_df.columns = ['team', 'confed']

# Map corrected names back to original names
dictionary_df = pd.read_csv('/home/albertovth/SPI/dictionary.csv')
corrected_to_original = pd.Series(dictionary_df['original'].values, index=dictionary_df['corrected']).to_dict()

# Correct the team names in the SPI data
spi_df['team'] = spi_df['team'].map(corrected_to_original).fillna(spi_df['team'])

# Correct the team names in the match data
df['home_team'] = df['home_team'].map(corrected_to_original).fillna(df['home_team'])
df['away_team'] = df['away_team'].map(corrected_to_original).fillna(df['away_team'])

# Filter data for the last four years and up to today's date
today = datetime.today()
four_years_ago = today - timedelta(days=4*365)
df['date'] = pd.to_datetime(df['date'])
filtered_df = df[(df['date'] >= four_years_ago) & (df['date'] <= today)]

# Remove matches with NaN scores
filtered_df = filtered_df.dropna(subset=['home_score', 'away_score'])

# Adjust goal counts based on match type
def adjust_goals(row):
    if row['tournament'] == 'Friendly':
        return row['home_score'] * 0.5, row['away_score'] * 0.5
    else:
        return row['home_score'], row['away_score']

filtered_df[['home_score', 'away_score']] = filtered_df.apply(lambda row: pd.Series(adjust_goals(row)), axis=1)

# Only include teams from the specified confederations
filtered_df = filtered_df[(filtered_df['home_team'].isin(confed_df['team'])) & (filtered_df['away_team'].isin(confed_df['team']))]

# Calculate match factors based on SPI
spi_factors = spi_df.set_index('team')['spi']

# Initialize points for xG and xGA
points_for_xG_high = {team: 0 for team in spi_df['team']}
points_for_xGA_high = {team: 0 for team in spi_df['team']}
points_for_xG_low = {team: 0 for team in spi_df['team']}
points_for_xGA_low = {team: 0 for team in spi_df['team']}

# High SPI teams
high_spi_teams = spi_df[spi_df['spi'] >= twenty_fifth_percentile_spi]['team'].tolist()

# Low SPI teams
low_spi_teams = spi_df[spi_df['spi'] < twenty_fifth_percentile_spi]['team'].tolist()

# Define the functions to calculate points
def calculate_points_high(row, median_spi, twenty_fifth_percentile_spi):
    home_team = row['home_team']
    away_team = row['away_team']
    
    spi_team1 = spi_factors.get(home_team, 1)
    spi_team2 = spi_factors.get(away_team, 1)
    
    adjusted_home_goals = row['home_score'] * 2 * (spi_team2 / twenty_fifth_percentile_spi) - row['home_score'] * 2 * (median_spi / spi_team1)
    adjusted_away_goals = row['away_score'] * 2 * (spi_team1 / twenty_fifth_percentile_spi) - row['away_score'] * 2 * (median_spi / spi_team2)
    
    # Cap points per match at 6
    adjusted_home_goals = min(adjusted_home_goals, 6)
    adjusted_away_goals = min(adjusted_away_goals, 6)
    
    points_for_xG_high[home_team] += max(adjusted_home_goals, 0.01)
    points_for_xGA_high[home_team] += max(adjusted_away_goals, 0.01)
    points_for_xG_high[away_team] += max(adjusted_away_goals, 0.01)
    points_for_xGA_high[away_team] += max(adjusted_home_goals, 0.01)

def calculate_points_low(row, twenty_fifth_percentile_spi):
    home_team = row['home_team']
    away_team = row['away_team']
    
    # Cap points per match at 6
    home_score_adjusted = min(row['home_score'] * 0.16, 6)
    away_score_adjusted = min(row['away_score'] * 6, 6)
    
    points_for_xG_low[home_team] += home_score_adjusted
    points_for_xGA_low[home_team] += away_score_adjusted
    points_for_xG_low[away_team] += min(row['away_score'] * 0.16, 6)
    points_for_xGA_low[away_team] += min(row['home_score'] * 6, 6)

# Apply the functions to calculate points
filtered_df.apply(lambda row: calculate_points_high(row, median_spi, twenty_fifth_percentile_spi) if row['home_team'] in high_spi_teams and row['away_team'] in high_spi_teams else calculate_points_low(row, twenty_fifth_percentile_spi), axis=1)

# Combine the points
points_for_xG = {team: points_for_xG_high[team] + points_for_xG_low[team] for team in spi_df['team']}
points_for_xGA = {team: points_for_xGA_high[team] + points_for_xGA_low[team] for team in spi_df['team']}

# Calculate matches played
matches_played = filtered_df['home_team'].value_counts() + filtered_df['away_team'].value_counts()
matches_played = matches_played.to_dict()

# Calculate xG and xGA
xg_data = []
for team in points_for_xG.keys():
    matches = matches_played.get(team, 1)  # Default to 1 to avoid division by zero
    xg = points_for_xG[team] / matches
    xga = points_for_xGA[team] / matches
    xg_data.append({'team': team, 'xG': xg, 'xGA': xga})

xg_df = pd.DataFrame(xg_data)

# Merge with confederations data to filter out only the relevant teams
xg_df = xg_df.merge(confed_df, on='team')

# Save the aggregated data to a new CSV file
xg_df.to_csv('/home/albertovth/SPI/aggregated_xg_data.csv', index=False)

# Separate and save data for each confederation, without the 'confed' column
conmebol_teams = xg_df[xg_df['confed'] == 'CONMEBOL'].drop(columns=['confed'])
uefa_teams = xg_df[xg_df['confed'] == 'UEFA'].drop(columns=['confed'])
concacaf_teams = xg_df[xg_df['confed'] == 'CONCACAF'].drop(columns=['confed'])

conmebol_teams.to_csv('/home/albertovth/SPI/CONMEBOL.csv', index=False)
uefa_teams.to_csv('/home/albertovth/SPI/UEFA.csv', index=False)
concacaf_teams.to_csv('/home/albertovth/SPI/CONCACAF.csv', index=False)

print("Data saved to CONMEBOL.csv, UEFA.csv, and CONCACAF.csv.")

