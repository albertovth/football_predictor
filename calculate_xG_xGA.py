import pandas as pd
from datetime import datetime, timedelta

# Load the match data
url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
df = pd.read_csv(url)

# Load the SPI data
spi_df = pd.read_csv('/home/albertovth/SPI/spi_final.csv')
spi_df = spi_df.rename(columns={'name': 'team'})

# Calculate the median SPI for the three confederations combined
median_spi = spi_df['spi'].median()
print(f"Median SPI: {median_spi}")

# Load the confederations data
confed_df = pd.read_csv('/home/albertovth/SPI/confederations.csv')
confed_df.columns = ['team', 'confed']

# Map corrected names back to original names
dictionary_df = pd.read_csv('/home/albertovth/SPI/dictionary.csv')
corrected_to_original = pd.Series(dictionary_df['original'].values, index=dictionary_df['corrected']).to_dict()

# Correct the team names in the SPI data
spi_df['team'] = spi_df['team'].map(corrected_to_original).fillna(spi_df['team'])

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

# Adjust goals based on the opponent's SPI
def adjust_goals_based_on_opponent_spi(row, median_spi):  
    home_team = row['home_team']
    away_team = row['away_team']
    
    if home_team not in spi_factors.index or away_team not in spi_factors.index:
        print(f"Team not found in SPI data: Home team = {home_team}, Away team = {away_team}")
        return pd.Series([row['home_score'], row['away_score']])  # Return original goals if any team is missing in spi_factors
    
    spi_team1 = spi_factors.get(home_team, 1)
    spi_team2 = spi_factors.get(away_team, 1)
    
    adjusted_home_goals = row['home_score'] * (spi_team2/median_spi)
    adjusted_away_goals = row['away_score'] * (spi_team1/median_spi)

    # Cap adjusted goals at 6
    adjusted_home_goals = min(adjusted_home_goals, 6)
    adjusted_away_goals = min(adjusted_away_goals, 6)

    return pd.Series([adjusted_home_goals, adjusted_away_goals])

# Apply the goal adjustments with capping
filtered_df[['adj_home_score', 'adj_away_score']] = filtered_df.apply(lambda row: adjust_goals_based_on_opponent_spi(row, median_spi), axis=1)

# Debug print statements to verify the adjusted goals
print("Adjusted Goals Sample:")
print(filtered_df[['home_team', 'away_team', 'home_score', 'away_score', 'adj_home_score', 'adj_away_score']].head())

# Calculate proxy xG and xGA
xg_data = []

for index, row in filtered_df.iterrows():
    home_team = row['home_team']
    away_team = row['away_team']
    home_goals = row['adj_home_score']
    away_goals = row['adj_away_score']

    xg_data.append({'team': home_team, 'xG': home_goals, 'xGA': away_goals})
    xg_data.append({'team': away_team, 'xG': away_goals, 'xGA': home_goals})

# Debug print statement to verify xG data
print("xG Data Sample:")
print(xg_data[:10])

xg_df = pd.DataFrame(xg_data)

# Aggregate data to get average xG and xGA per team
aggregated_data = xg_df.groupby('team').agg({
    'xG': 'mean',
    'xGA': 'mean'
}).reset_index()

# Merge with confederations data to filter out only the relevant teams
aggregated_data = aggregated_data.merge(confed_df, on='team')

print("CONCACAF teams in aggregated data:")
print(aggregated_data[aggregated_data['confed'] == 'CONCACAF']['team'].unique())

# Debug print statement to verify aggregated xG data
print("Aggregated xG Data Sample:")
print(aggregated_data[aggregated_data['confed'] == 'CONCACAF'])


# Save the aggregated data to a new CSV file
aggregated_data.to_csv('/home/albertovth/SPI/aggregated_xg_data.csv', index=False)

# Separate and save data for each confederation, without the 'confed' column
conmebol_teams = aggregated_data[aggregated_data['confed'] == 'CONMEBOL'].drop(columns=['confed'])
uefa_teams = aggregated_data[aggregated_data['confed'] == 'UEFA'].drop(columns=['confed'])
concacaf_teams = aggregated_data[aggregated_data['confed'] == 'CONCACAF'].drop(columns=['confed'])

conmebol_teams.to_csv('/home/albertovth/SPI/CONMEBOL.csv', index=False)
uefa_teams.to_csv('/home/albertovth/SPI/UEFA.csv', index=False)
concacaf_teams.to_csv('/home/albertovth/SPI/CONCACAF.csv', index=False)

print("Data saved to CONMEBOL.csv, UEFA.csv, and CONCACAF.csv.")

