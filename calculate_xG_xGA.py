import pandas as pd
from datetime import datetime, timedelta

# Load the match data
url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
df = pd.read_csv(url)

# Load the SPI data
spi_df = pd.read_csv('/home/albertovth/SPI/spi_final.csv')
spi_df = spi_df.rename(columns={'name': 'team'})

cutoff_quantile_low_teams=0.07 #Calculated with calculate_low_team_cutoff.py

# Calculate the median SPI, 25th percentile SPI and the minimum SPI for the three confederations combined
median_spi = spi_df['spi'].median()
cutoff_quantile_spi = spi_df['spi'].quantile(cutoff_quantile_low_teams)
minimum_spi = spi_df['spi'].min()
maximum_spi = spi_df['spi'].max()

print(f"Median SPI: {median_spi}")
print(f"First Percentile SPI: {cutoff_quantile_spi}")
print(f"Minimum SPI: {minimum_spi}")

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

# Filter data from May 23, 2021, and up to today's date
today = datetime.today()
start_date = pd.to_datetime('2021-05-23')
df['date'] = pd.to_datetime(df['date'])
filtered_df = df[(df['date'] >= start_date) & (df['date'] <= today)]

# Remove matches with NaN scores
filtered_df = filtered_df.dropna(subset=['home_score', 'away_score'])

# Adjust goal counts based on match type
def adjust_goals(row):
    if row['tournament'] == 'Friendly':
        return row['home_score'] * 0.5, row['away_score'] * 0.5
    else:
        return row['home_score'], row['away_score']

filtered_df[['home_score', 'away_score']] = filtered_df.apply(lambda row: pd.Series(adjust_goals(row)), axis=1)

# Only include matches where both teams are in the SPI data
filtered_df = filtered_df[(filtered_df['home_team'].isin(spi_df['team'])) & (filtered_df['away_team'].isin(spi_df['team']))]

# Calculate match factors based on SPI
spi_factors = spi_df.set_index('team')['spi']

# Initialize points for xG and xGA
points_for_xG_high = {team: 0 for team in spi_df['team']}
points_for_xGA_high = {team: 0 for team in spi_df['team']}
points_for_xG_low = {team: 0 for team in spi_df['team']}
points_for_xGA_low = {team: 0 for team in spi_df['team']}


# High SPI teams
high_spi_teams = spi_df[spi_df['spi'] >= cutoff_quantile_spi]['team'].tolist()

# Low SPI teams
low_spi_teams = spi_df[spi_df['spi'] < cutoff_quantile_spi]['team'].tolist()

# Define the functions to calculate points
def calculate_points_high(row, maximum_spi, minimum_spi):
    home_team = row['home_team']
    away_team = row['away_team']
    
    if home_team not in spi_factors or away_team not in spi_factors:
        return
    
    spi_team1 = spi_factors.get(home_team, 1)
    spi_team2 = spi_factors.get(away_team, 1)
    
    adjustment_factor=0.017 # calculated with adjustment_factor_calculate_and_dynamism_variable.py
    dynamism_variable=0.16 # calculated with adjustment_factor_calculate_and_dynamism_variable.py
    
    adjusted_home_goals = row['home_score'] * adjustment_factor * (spi_team2 / (minimum_spi - dynamism_variable)) - adjustment_factor * row['home_score'] * ((maximum_spi + dynamism_variable) / spi_team1)
    adjusted_away_goals = row['away_score'] * adjustment_factor * (spi_team1 / (minimum_spi - dynamism_variable)) - adjustment_factor * row['away_score'] * ((maximum_spi + dynamism_variable) / spi_team2)

    
    # Cap points per match at 6
    adjusted_home_goals = min(adjusted_home_goals, 6)
    adjusted_away_goals = min(adjusted_away_goals, 6)
    
    points_for_xG_high[home_team] += max(adjusted_home_goals, 0.01)
    points_for_xGA_high[home_team] += max(adjusted_away_goals, 0.01)
    points_for_xG_high[away_team] += max(adjusted_away_goals, 0.01)
    points_for_xGA_high[away_team] += max(adjusted_home_goals, 0.01)

def calculate_points_low(row, cutoff_quantile_spi):
    home_team = row['home_team']
    away_team = row['away_team']
    
    if home_team not in points_for_xG_low or away_team not in points_for_xG_low:
        return
    
    # Cap points per match at 6
       
    points_for_xG_low[home_team] += min(row['home_score']*0.17, 6)
    points_for_xGA_low[home_team] += min(row['away_score']*6, 6)
    points_for_xG_low[away_team] += min(row['away_score']*0.17, 6)
    points_for_xGA_low[away_team] += min(row['home_score']*6, 6)

# Apply the functions to calculate points
filtered_df.apply(lambda row: calculate_points_high(row, maximum_spi, minimum_spi) if row['home_team'] in high_spi_teams and row['away_team'] in high_spi_teams else calculate_points_low(row, cutoff_quantile_spi), axis=1)

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
nan_teams = {team: (avg_spi, med_spi) for team, avg_spi, med_spi in zip(average_opponent_spi.keys(), average_opponent_spi.values(), median_opponent_spi.values()) if pd.isna(avg_spi) or pd.isna(med_spi)}

print("Teams with NaN values in average or median opponent SPI:")
for team, (avg_spi, med_spi) in nan_teams.items():
    print(f"{team}: Average SPI={avg_spi}, Median SPI={med_spi}")

# Save average and median opponent SPI to a new CSV file
opponent_spi_data = [{'team': team, 'average_opponent_spi': avg_spi, 'median_opponent_spi': med_spi} for team, avg_spi, med_spi in zip(average_opponent_spi.keys(), average_opponent_spi.values(), median_opponent_spi.values())]
opponent_spi_df = pd.DataFrame(opponent_spi_data)
opponent_spi_df.to_csv('/home/albertovth/SPI/opponent_spi_data.csv', index=False)

print("Average and median opponent SPI data saved to opponent_spi_data.csv")

# Compute medians for adjustment
median_xG = xg_df['xG'].median()
median_xGA = xg_df['xGA'].median()

# Load historical data
historical_data = pd.read_csv('https://raw.githubusercontent.com/martj42/international_results/master/results.csv')

# Filter data from May 23, 2021, and up to today's date
historical_data['date'] = pd.to_datetime(historical_data['date'])
start_date = pd.to_datetime('2021-05-23')
today = datetime.today()
filtered_data = historical_data[(historical_data['date'] >= start_date) & (historical_data['date'] <= today)]


all_goals = pd.concat([filtered_data['home_score'], filtered_data['away_score']])
median_goals_per_team = all_goals.median()

# Apply the multiplicative adjustment
xg_df['xG'] = (xg_df['xG'] / median_xG) * median_goals_per_team
xg_df['xGA'] = (xg_df['xGA'] / median_xGA) * median_goals_per_team

# Merge with confederations data to filter out only the relevant teams
xg_df = xg_df.merge(confed_df, on='team')

# Save the aggregated data to a new CSV file
xg_df.to_csv('/home/albertovth/SPI/aggregated_xg_data.csv', index=False)

# Separate and save data for each confederation, without the 'confed' column
conmebol_teams = xg_df[xg_df['confed'] == 'CONMEBOL'].drop(columns=['confed'])
uefa_teams = xg_df[xg_df['confed'] == 'UEFA'].drop(columns=['confed'])
concacaf_teams = xg_df[xg_df['confed'] == 'CONCACAF'].drop(columns=['confed'])
afc_teams = xg_df[xg_df['confed'] == 'AFC'].drop(columns=['confed'])
caf_teams = xg_df[xg_df['confed'] == 'CAF'].drop(columns=['confed'])
ofc_teams = xg_df[xg_df['confed'] == 'OFC'].drop(columns=['confed'])

conmebol_teams.to_csv('/home/albertovth/SPI/CONMEBOL.csv', index=False)
uefa_teams.to_csv('/home/albertovth/SPI/UEFA.csv', index=False)
concacaf_teams.to_csv('/home/albertovth/SPI/CONCACAF.csv', index=False)
afc_teams.to_csv('/home/albertovth/SPI/AFC.csv', index=False)
caf_teams.to_csv('/home/albertovth/SPI/CAF.csv', index=False)
ofc_teams.to_csv('/home/albertovth/SPI/OFC.csv', index=False)