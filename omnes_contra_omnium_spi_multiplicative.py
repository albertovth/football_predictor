import numpy as np
from scipy.stats import poisson
import pandas as pd
from tqdm import tqdm



# Load historical data
historical_data = pd.read_csv('https://raw.githubusercontent.com/martj42/international_results/master/results.csv')

# Filter data for the past 4 years
historical_data['date'] = pd.to_datetime(historical_data['date'])
filtered_data = historical_data[historical_data['date'] >= pd.Timestamp.now() - pd.DateOffset(years=4)]


# Calculate median goals
all_goals = pd.concat([filtered_data['home_score'], filtered_data['away_score']])
median_goals_home = all_goals.median()
median_goals_away = all_goals.median()

def inverse_poisson(lam, rand_nums):
    goals = []
    for r in rand_nums:
        cum_prob = 0
        k = 0
        while cum_prob < r:
            cum_prob += poisson.pmf(k, lam)
            k += 1
        goals.append(k - 1)
    return goals

def run_simulation(df):
    n_simulations = 10000
    results = {team: {'wins': 0, 'draws': 0, 'losses': 0} for team in df['team']}

    for i, team_a in tqdm(df.iterrows(), total=len(df), desc="Teams progress"):
        for j, team_b in tqdm(df.iterrows(), total=len(df), desc="Match progress", leave=False):
            if i != j:
                # Calculate expected goals using the multiplicative method with median goals
                expected_goals_team_a = (team_a['xG'] / df['xG'].median()) * (team_b['xGA'] / df['xGA'].median()) * median_goals_home
                expected_goals_team_b = (team_b['xG'] / df['xG'].median()) * (team_a['xGA'] / df['xGA'].median()) * median_goals_away

                rand_nums = np.random.rand(n_simulations)

                goals_team_a = inverse_poisson(expected_goals_team_a, rand_nums)
                goals_team_b = inverse_poisson(expected_goals_team_b, rand_nums)

                wins_team_a = np.sum(np.array(goals_team_a) > np.array(goals_team_b))
                draws = np.sum(np.array(goals_team_a) == np.array(goals_team_b))
                wins_team_b = np.sum(np.array(goals_team_a) < np.array(goals_team_b))

                results[team_a['team']]['wins'] += wins_team_a
                results[team_a['team']]['draws'] += draws
                results[team_a['team']]['losses'] += wins_team_b
                results[team_b['team']]['wins'] += wins_team_b
                results[team_b['team']]['draws'] += draws
                results[team_b['team']]['losses'] += wins_team_a

    total_matches_per_team = 2 * (len(df) - 1) * n_simulations

    for team, res in results.items():
        res['points'] = res['wins'] * 3 + res['draws']
        res['avg_points_per_match'] = res['points'] / total_matches_per_team
        res['spi'] = (res['avg_points_per_match'] / 3) * 100

    return results


def run_combined_simulation(file_paths, output_file):
    # Load individual CSVs
    spi_conmebol = pd.read_csv(file_paths[0])
    spi_uefa = pd.read_csv(file_paths[1])
    spi_concacaf = pd.read_csv(file_paths[2])
    spi_afc = pd.read_csv(file_paths[3])
    spi_caf = pd.read_csv(file_paths[4])
    spi_ofc = pd.read_csv(file_paths[5])

    # Add confederation column
    spi_conmebol['confed'] = 'CONMEBOL'
    spi_uefa['confed'] = 'UEFA'
    spi_concacaf['confed'] = 'CONCACAF'
    spi_afc['confed'] = 'AFC'
    spi_caf['confed'] = 'CAF'
    spi_ofc['confed'] = 'OFC'

    # Combine data
    combined_df = pd.concat([spi_conmebol, spi_uefa, spi_concacaf, spi_afc, spi_caf, spi_ofc], ignore_index=True)

    # Run simulations
    results = run_simulation(combined_df)

    # Convert results to DataFrame
    results_df = pd.DataFrame.from_dict(results, orient='index').reset_index()
    results_df.rename(columns={'index': 'team'}, inplace=True)

    # Merge with xG and xGA
    spi_df = combined_df.merge(results_df[['team', 'spi']], on='team')

    # Scale xG and xGA values
    match_data = pd.read_csv("https://raw.githubusercontent.com/martj42/international_results/master/results.csv")
    match_data['date'] = pd.to_datetime(match_data['date'])
    match_data = match_data[match_data['date'] >= pd.Timestamp.now() - pd.DateOffset(years=4)]

    median_actual_goals_scored = match_data[['home_score', 'away_score']].stack().median()
    median_actual_goals_conceded = match_data[['home_score', 'away_score']].stack().median()

    xg_median = spi_df['xG'].median()
    xga_median = spi_df['xGA'].median()

    spi_df['xG'] = spi_df['xG'] * (median_actual_goals_scored / xg_median)
    spi_df['xGA'] = spi_df['xGA'] * (median_actual_goals_conceded / xga_median)

    # Normalize Off (xG) and Def (xGA) values again after scaling
    spi_df['off'] = spi_df['xG']
    spi_df['def'] = spi_df['xGA']
       
    # Read the dictionary CSV for name corrections
    dictionary_df = pd.read_csv('/home/albertovth/SPI/dictionary.csv')
    name_mapping = pd.Series(dictionary_df.corrected.values, index=dictionary_df.original).to_dict()

    # Apply name mapping
    spi_df['team'] = spi_df['team'].map(name_mapping).fillna(spi_df['team'])
   
    # Rank teams
    spi_df['rank'] = spi_df['spi'].rank(method='first', ascending=False).astype(int)
    spi_df = spi_df.rename(columns={'team': 'name'})
    spi_df = spi_df[['rank', 'name', 'confed', 'off', 'def', 'spi']]
    spi_df = spi_df.sort_values(by=['spi', 'name'], ascending=[False, True])

    # Save the final results
    spi_df.to_csv(f'/home/albertovth/SPI/{output_file}.csv', index=False)

    print("SPI Combined Results:")
    print(spi_df)

# Run combined simulation for all teams
run_combined_simulation([
    '/home/albertovth/SPI/CONMEBOL.csv',
    '/home/albertovth/SPI/UEFA.csv',
    '/home/albertovth/SPI/CONCACAF.csv',
    '/home/albertovth/SPI/AFC.csv',
    '/home/albertovth/SPI/CAF.csv',
    '/home/albertovth/SPI/OFC.csv'
], 'spi_final')
