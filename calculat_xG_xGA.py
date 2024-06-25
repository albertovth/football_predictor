import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import numpy as np

# Load the match data
url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
df = pd.read_csv(url)

# Load the SPI data
spi_df = pd.read_csv('/home/albertovth/SPI/spi_final.csv')
spi_df = spi_df.rename(columns={'name': 'team'})

# Load the confederations data
confed_df = pd.read_csv('/home/albertovth/SPI/confederations.csv')
confed_df.columns = ['team', 'confed']

# Map corrected names back to original names
dictionary_df = pd.read_csv('/home/albertovth/SPI/dictionary.csv')
corrected_to_original = pd.Series(dictionary_df['original'].values, index=dictionary_df['corrected']).to_dict()

# Filter data for the last two years
today = datetime.today()
two_years_ago = today - timedelta(days=4*365)
df['date'] = pd.to_datetime(df['date'])
filtered_df = df[df['date'] >= two_years_ago]

# Adjust goal counts based on match type
def adjust_goals(row):
    if row['tournament'] == 'Friendly':
        return row['home_score'] * 0.5, row['away_score'] * 0.5
    else:
        return row['home_score'], row['away_score']

filtered_df[['home_score', 'away_score']] = filtered_df.apply(lambda row: pd.Series(adjust_goals(row)), axis=1)

# Only include teams from the specified confederations
filtered_df['home_team'] = filtered_df['home_team'].map(corrected_to_original).fillna(filtered_df['home_team'])
filtered_df['away_team'] = filtered_df['away_team'].map(corrected_to_original).fillna(filtered_df['away_team'])
filtered_df = filtered_df[(filtered_df['home_team'].isin(confed_df['team'])) & (filtered_df['away_team'].isin(confed_df['team']))]

# Calculate SPI factors
spi_factors = spi_df.set_index('team')['spi']

# Calculate expected goals adjustment based on SPI factors
def adjust_goals_based_on_spi(row, slope_home, intercept_home, slope_away, intercept_away):
    team1 = row['home_team']
    team2 = row['away_team']
    if team1 not in spi_factors.index or team2 not in spi_factors.index:
        return pd.Series([row['home_score'], row['away_score']])  # Return original goals if any team is missing in spi_factors
    spi_factor1 = spi_factors.get(team1, 1)
    spi_factor2 = spi_factors.get(team2, 1)
    match_factor = spi_factor1 / spi_factor2

    home_goals = row['home_score']
    away_goals = row['away_score']

    expected_home_goals = match_factor * slope_home + intercept_home
    expected_away_goals = (1 / match_factor) * slope_away + intercept_away

    adjusted_home_goals = home_goals * (home_goals / expected_home_goals) if expected_home_goals != 0 else home_goals
    adjusted_away_goals = away_goals * (away_goals / expected_away_goals) if expected_away_goals != 0 else away_goals

    # Ensure no negative goals
    adjusted_home_goals = max(0, adjusted_home_goals)
    adjusted_away_goals = max(0, adjusted_away_goals)

    return pd.Series([adjusted_home_goals, adjusted_away_goals])

# Calculate the regression slopes using actual goals and match factors
match_factors = []
home_goals_list = []
away_goals_list = []

for index, row in filtered_df.iterrows():
    team1 = row['home_team']
    team2 = row['away_team']
    if team1 in spi_df['team'].values and team2 in spi_df['team'].values:
        spi_team1 = spi_df[spi_df['team'] == team1]['spi'].values[0]
        spi_team2 = spi_df[spi_df['team'] == team2]['spi'].values[0]
        match_factor = spi_team1 / spi_team2
        match_factors.append(match_factor)
        home_goals_list.append(row['home_score'])
        away_goals_list.append(row['away_score'])

match_factors = np.array(match_factors).reshape(-1, 1)
inverse_match_factors = 1 / match_factors
home_goals_list = np.array(home_goals_list)
away_goals_list = np.array(away_goals_list)

# Remove NaN values
valid_indices_home = ~np.isnan(home_goals_list)
valid_indices_away = ~np.isnan(away_goals_list)

match_factors_home = match_factors[valid_indices_home]
home_goals_list = home_goals_list[valid_indices_home]

match_factors_away = inverse_match_factors[valid_indices_away]
away_goals_list = away_goals_list[valid_indices_away]

# Linear regression with intercept for home goals
reg_home = LinearRegression().fit(match_factors_home, home_goals_list)
slope_home = reg_home.coef_[0]
intercept_home = reg_home.intercept_

# Linear regression with intercept for away goals
reg_away = LinearRegression().fit(match_factors_away, away_goals_list)
slope_away = reg_away.coef_[0]
intercept_away = reg_away.intercept_

print(f"Correlation between SPI factors and home goals: {reg_home.score(match_factors_home, home_goals_list)}")
print(f"Regression slope for home goals: {slope_home}, intercept: {intercept_home}")
print(f"Correlation between SPI factors and away goals: {reg_away.score(match_factors_away, away_goals_list)}")
print(f"Regression slope for away goals: {slope_away}, intercept: {intercept_away}")

# Adjust goals based on SPI factors using the calculated slope
filtered_df[['home_score', 'away_score']] = filtered_df.apply(lambda row: adjust_goals_based_on_spi(row, slope_home, intercept_home, slope_away, intercept_away), axis=1)

# Calculate proxy xG and xGA
xg_data = []

for index, row in filtered_df.iterrows():
    home_team = row['home_team']
    away_team = row['away_team']
    home_goals = row['home_score']
    away_goals = row['away_score']

    xg_data.append({'team': home_team, 'xG': home_goals})
    xg_data.append({'team': away_team, 'xGA': home_goals})
    xg_data.append({'team': away_team, 'xG': away_goals})
    xg_data.append({'team': home_team, 'xGA': away_goals})

xg_df = pd.DataFrame(xg_data)

# Aggregate data to get average xG and xGA per team
aggregated_data = xg_df.groupby('team').agg({
    'xG': 'mean',
    'xGA': 'mean'
}).reset_index()

# Merge with confederations data to filter out only the relevant teams
aggregated_data = aggregated_data.merge(confed_df, on='team')

# Ensure no negative xG and xGA values
aggregated_data['xG'] = aggregated_data['xG'].apply(lambda x: max(0, x))
aggregated_data['xGA'] = aggregated_data['xGA'].apply(lambda x: max(0, x))

# Save the aggregated data to a new CSV file
aggregated_data.to_csv('/home/albertovth/SPI/aggregated_xg_data.csv', index=False)

# Separate and save data for each confederation, without the 'confed' column
conmebol_teams = aggregated_data[aggregated_data['confed'] == 'CONMEBOL'].drop(columns=['confed'])
uefa_teams = aggregated_data[aggregated_data['confed'] == 'UEFA'].drop(columns=['confed'])
concacaf_teams = aggregated_data[aggregated_data['confed'] == 'CONCACAF'].drop(columns=['confed'])

conmebol_teams.to_csv('/home/albertovth/SPI/CONMEBOL.csv', index=False)
uefa_teams.to_csv('/home/albertovth/SPI/UEFA.csv', index=False)
concacaf_teams.to_csv('/home/albertovth/SPI/CONCACAF.csv', index=False)

print("Aggregated xG Data:")
print(aggregated_data.head())
print("Data saved to CONMEBOL.csv, UEFA.csv, and CONCACAF.csv.")




