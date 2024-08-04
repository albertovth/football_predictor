import numpy as np
from scipy.stats import poisson
import pandas as pd
from tqdm import tqdm
from datetime import datetime

# Load historical data
historical_data = pd.read_csv('https://raw.githubusercontent.com/martj42/international_results/master/results.csv')

# Filter data from May 23, 2021, and up to today's date
historical_data['date'] = pd.to_datetime(historical_data['date'])
start_date = pd.to_datetime('2021-05-23')
today = datetime.today()
filtered_data = historical_data[(historical_data['date'] >= start_date) & (historical_data['date'] <= today)]

# Calculate median goals
all_goals = pd.concat([filtered_data['home_score'], filtered_data['away_score']])
median_goals_home = all_goals.median()
median_goals_away = all_goals.median()
median_goals = all_goals.median()

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
   
    # Scale xG and xGA to median values
    df['xG_scaled_to_median'] = (df['xG'] / df['xG'].median()) * median_goals
    df['xGA_scaled_to_median'] = (df['xGA'] / df['xGA'].median()) * median_goals

    # Calculate the maximum xG and xGA
    max_xG = df['xG_scaled_to_median'].max()
    max_xGA = df['xGA_scaled_to_median'].max()

    # Scale the xG and xGA values proportionally to cap at 3.5 and 6 respectively
    df['xG_scaled'] = df['xG_scaled_to_median'] * (3.5 / max_xG)
    df['xGA_scaled'] = df['xGA_scaled_to_median'] * (6.0 / max_xGA)

    for i, team_a_row in tqdm(df.iterrows(), total=len(df), desc="Teams progress"):
        for j, team_b_row in tqdm(df.iterrows(), total=len(df), desc="Match progress", leave=False):
            if i != j:
                team_a = team_a_row['team']
                team_b = team_b_row['team']

                # Calculate expected goals using the additive method
                expected_goals_team_a = (team_a_row['xG_scaled'] + team_b_row['xGA_scaled']) / 2
                expected_goals_team_b = (team_b_row['xG_scaled'] + team_a_row['xGA_scaled']) / 2
               
                rand_nums = np.random.rand(n_simulations)

                goals_team_a = inverse_poisson(expected_goals_team_a, rand_nums)
                goals_team_b = inverse_poisson(expected_goals_team_b, rand_nums)

                wins_team_a = np.sum(np.array(goals_team_a) > np.array(goals_team_b))
                draws = np.sum(np.array(goals_team_a) == np.array(goals_team_b))
                wins_team_b = np.sum(np.array(goals_team_a) < np.array(goals_team_b))

                results[team_a]['wins'] += wins_team_a
                results[team_a]['draws'] += draws
                results[team_a]['losses'] += wins_team_b
                results[team_b]['wins'] += wins_team_b
                results[team_b]['draws'] += draws
                results[team_b]['losses'] += wins_team_a

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

    # Scale xG and xGA values to median goals
    spi_df['xG_scaled_to_median'] = (spi_df['xG'] / spi_df['xG'].median()) * median_goals
    spi_df['xGA_scaled_to_median'] = (spi_df['xGA'] / spi_df['xGA'].median()) * median_goals

    # Calculate the maximum xG and xGA
    max_xG = spi_df['xG_scaled_to_median'].max()
    max_xGA = spi_df['xGA_scaled_to_median'].max()

    # Scale the xG and xGA values proportionally to cap at 3.5 and 6 respectively
    spi_df['xG_scaled'] = spi_df['xG_scaled_to_median'] * (3.5 / max_xG)
    spi_df['xGA_scaled'] = spi_df['xGA_scaled_to_median'] * (6.0 / max_xGA)

    # Normalize Off (xG) and Def (xGA) values
    spi_df['off'] = spi_df['xG_scaled']
    spi_df['def'] = spi_df['xGA_scaled']
       
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
