import pandas as pd
from datetime import datetime, timedelta

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

# Filter data for the last four years
today = datetime.today()
four_years_ago = today - timedelta(days=4*365)
df['date'] = pd.to_datetime(df['date'])
filtered_df = df[df['date'] >= four_years_ago]

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

# Calculate match factors based on SPI
spi_factors = spi_df.set_index('team')['spi']

# Calculate expected goals based on Off and Def metrics
def calculate_expected_goals(row):
    team1 = row['home_team']
    team2 = row['away_team']
    
    if team1 not in spi_factors.index or team2 not in spi_factors.index:
        return pd.Series([None, None])
    
    spi_team1 = spi_factors.get(team1, 1)
    spi_team2 = spi_factors.get(team2, 1)
    off_team1 = spi_df[spi_df['team'] == team1]['off'].values[0]
    def_team1 = spi_df[spi_df['team'] == team1]['def'].values[0]
    off_team2 = spi_df[spi_df['team'] == team2]['off'].values[0]
    def_team2 = spi_df[spi_df['team'] == team2]['def'].values[0]
   
    match_factor = spi_team1 / spi_team2
   
    expected_home_goals = ((off_team1 + def_team2) / 2) * match_factor
    expected_away_goals = ((off_team2 + def_team1) / 2) / match_factor

    return pd.Series([expected_home_goals, expected_away_goals])

# Apply the expected goals calculation
filtered_df[['expected_home_goals', 'expected_away_goals']] = filtered_df.apply(lambda row: calculate_expected_goals(row), axis=1)

# Adjust goals based on the expected goals with capping
def adjust_goals_based_on_expected(row, cap_value=6):
    if pd.isna(row['expected_home_goals']) or pd.isna(row['expected_away_goals']):
        return pd.Series([row['home_score'], row['away_score']])
    
    home_goals = row['home_score']
    away_goals = row['away_score']
    expected_home_goals = row['expected_home_goals']
    expected_away_goals = row['expected_away_goals']

    adjusted_home_goals = min(home_goals * (home_goals / expected_home_goals), cap_value) if expected_home_goals != 0 else home_goals
    adjusted_away_goals = min(away_goals * (away_goals / expected_away_goals), cap_value) if expected_away_goals != 0 else away_goals

    return pd.Series([adjusted_home_goals, adjusted_away_goals])

# Apply the goal adjustments with capping
filtered_df[['home_score', 'away_score']] = filtered_df.apply(lambda row: adjust_goals_based_on_expected(row), axis=1)

# Calculate proxy xG and xGA
xg_data = []

for index, row in filtered_df.iterrows():
    home_team = row['home_team']
    away_team = row['away_team']
    home_goals = row['home_score']
    away_goals = row['away_score']

    xg_data.append({'team': home_team, 'xG': home_goals, 'xGA': away_goals})
    xg_data.append({'team': away_team, 'xG': away_goals, 'xGA': home_goals})

xg_df = pd.DataFrame(xg_data)

# Aggregate data to get average xG and xGA per team
aggregated_data = xg_df.groupby('team').agg({
    'xG': 'mean',
    'xGA': 'mean'
}).reset_index()

# Merge with confederations data to filter out only the relevant teams
aggregated_data = aggregated_data.merge(confed_df, on='team')

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





