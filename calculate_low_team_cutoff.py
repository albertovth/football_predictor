import pandas as pd
from datetime import datetime

# Load the SPI data
spi_df = pd.read_csv('/home/albertovth/SPI/spi_final.csv')
spi_df = spi_df.rename(columns={'name': 'team'})

# Set up the quantile range to explore
quantile_range = [0.01 * i for i in range(1, 26)]  # From 0.01 to 0.25

# Load the confederations and dictionary data
confed_df = pd.read_csv('/home/albertovth/SPI/confederations.csv')
confed_df.columns = ['team', 'confed']
dictionary_df = pd.read_csv('/home/albertovth/SPI/dictionary.csv')
corrected_to_original = pd.Series(dictionary_df['original'].values, index=dictionary_df['corrected']).to_dict()

# Apply the dictionary mapping to the SPI dataset
spi_df['team'] = spi_df['team'].map(corrected_to_original).fillna(spi_df['team'])

# Preprocess match data
url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
df = pd.read_csv(url)

# Correct the team names
df['home_team'] = df['home_team'].map(corrected_to_original).fillna(df['home_team'])
df['away_team'] = df['away_team'].map(corrected_to_original).fillna(df['away_team'])

# Filter to only include matches from teams present in the SPI data
spi_teams = spi_df['team'].tolist()
df = df[(df['home_team'].isin(spi_teams)) & (df['away_team'].isin(spi_teams))]

# Date filter
today = datetime.today()
start_date = pd.to_datetime('2021-05-23')
df['date'] = pd.to_datetime(df['date'])
filtered_df = df[(df['date'] >= start_date) & (df['date'] <= today)]

filtered_df = filtered_df.dropna(subset=['home_score', 'away_score'])

def adjust_goals(row):
    if row['tournament'] == 'Friendly':
        return row['home_score'] * 0.5, row['away_score'] * 0.5
    else:
        return row['home_score'], row['away_score']

filtered_df[['home_score', 'away_score']] = filtered_df.apply(lambda row: pd.Series(adjust_goals(row)), axis=1)
spi_factors = spi_df.set_index('team')['spi']

for cutoff_quantile_low_teams in quantile_range:
    # Calculate the median SPI, quantile SPI, min SPI, and max SPI
    median_spi = spi_df['spi'].median()
    cutoff_quantile_spi = spi_df['spi'].quantile(cutoff_quantile_low_teams)
    minimum_spi = spi_df['spi'].min()
    maximum_spi = spi_df['spi'].max()

    print(f"Testing with cutoff quantile: {cutoff_quantile_low_teams}")
    print(f"Cutoff Quantile SPI: {cutoff_quantile_spi}")

    points_for_xG_high = {team: 0 for team in spi_df['team']}
    points_for_xGA_high = {team: 0 for team in spi_df['team']}
    points_for_xG_low = {team: 0 for team in spi_df['team']}
    points_for_xGA_low = {team: 0 for team in spi_df['team']}

    high_spi_teams = spi_df[spi_df['spi'] >= cutoff_quantile_spi]['team'].tolist()
    low_spi_teams = spi_df[spi_df['spi'] < cutoff_quantile_spi]['team'].tolist()

    def calculate_points_high(row, maximum_spi, minimum_spi):
        home_team = row['home_team']
        away_team = row['away_team']

        if home_team not in spi_factors or away_team not in spi_factors:
            return

        spi_team1 = spi_factors.get(home_team, 1)
        spi_team2 = spi_factors.get(away_team, 1)

        adjustment_factor = 0.017
        dynamism_variable = 0.16

        adjusted_home_goals = row['home_score'] * adjustment_factor * (spi_team2 / (minimum_spi - dynamism_variable)) - adjustment_factor * row['home_score'] * ((maximum_spi + dynamism_variable) / spi_team1)
        adjusted_away_goals = row['away_score'] * adjustment_factor * (spi_team1 / (minimum_spi - dynamism_variable)) - adjustment_factor * row['away_score'] * ((maximum_spi + dynamism_variable) / spi_team2)

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

        home_score_adjusted = min(row['home_score'] * 0.17, 6)
        away_score_adjusted = min(row['away_score'] * 6, 6)

        points_for_xG_low[home_team] += home_score_adjusted
        points_for_xGA_low[home_team] += away_score_adjusted
        points_for_xG_low[away_team] += min(row['away_score'] * 0.17, 6)
        points_for_xGA_low[away_team] += min(row['home_score'] * 6, 6)

    filtered_df.apply(lambda row: calculate_points_high(row, maximum_spi, minimum_spi) if row['home_team'] in high_spi_teams and row['away_team'] in high_spi_teams else calculate_points_low(row, cutoff_quantile_spi), axis=1)

    points_for_xG = {team: points_for_xG_high[team] + points_for_xG_low[team] for team in spi_df['team']}
    points_for_xGA = {team: points_for_xGA_high[team] + points_for_xGA_low[team] for team in spi_df['team']}

    matches_played = filtered_df['home_team'].value_counts() + filtered_df['away_team'].value_counts()
    matches_played = matches_played.to_dict()

    xg_data = []
    for team in points_for_xG.keys():
        matches = matches_played.get(team, 1)
        xg = points_for_xG[team] / matches
        xga = points_for_xGA[team] / matches
        xg_data.append({'team': team, 'xG': xg, 'xGA': xga})

    xg_df = pd.DataFrame(xg_data)

    # Check if any teams have both xG and xGA below 1
    low_xg_xga_teams = xg_df[(xg_df['xG'] < 1) & (xg_df['xGA'] < 1)]
    
    if low_xg_xga_teams.empty:
        print(f"Found a suitable quantile: {cutoff_quantile_low_teams}")
        break
    else:
        print(f"Teams with xG and xGA both under 1 at quantile {cutoff_quantile_low_teams}:\n{low_xg_xga_teams}")

    print("-" * 50)

