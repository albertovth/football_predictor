import numpy as np
from scipy.stats import poisson
import pandas as pd

def run_simulation(file_path, output_prefix):
    df = pd.read_csv(file_path)

    # Function to calculate number of goals using inverse Poisson
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

    # Number of simulations
    n_simulations = 10000

    # Initialize results dictionary
    results = {team: {'wins': 0, 'draws': 0, 'losses': 0} for team in df['team']}

    # Simulate matches
    for i, team_a in df.iterrows():
        for j, team_b in df.iterrows():
            if i != j:
                # Expected goals
                expected_goals_team_a = (team_a['xG'] + team_b['xGA']) / 2
                expected_goals_team_b = (team_b['xG'] + team_a['xGA']) / 2

                # Random numbers
                rand_nums = np.random.rand(n_simulations)

                # Simulate goals using inverse_poisson
                goals_team_a = inverse_poisson(expected_goals_team_a, rand_nums)
                goals_team_b = inverse_poisson(expected_goals_team_b, rand_nums)

                # Calculate outcomes
                wins_team_a = np.sum(np.array(goals_team_a) > np.array(goals_team_b))
                draws = np.sum(np.array(goals_team_a) == np.array(goals_team_b))
                wins_team_b = np.sum(np.array(goals_team_a) < np.array(goals_team_b))

                # Update results
                results[team_a['team']]['wins'] += wins_team_a
                results[team_a['team']]['draws'] += draws
                results[team_a['team']]['losses'] += wins_team_b
                results[team_b['team']]['wins'] += wins_team_b
                results[team_b['team']]['draws'] += draws
                results[team_b['team']]['losses'] += wins_team_a

    # Calculate points and percentages
    total_matches_per_team = 2 * (len(df) - 1) * n_simulations

    for team, res in results.items():
        res['points'] = res['wins'] * 3 + res['draws']
        res['avg_points_per_match'] = res['points'] / total_matches_per_team
        res['SPI'] = (res['avg_points_per_match'] / 3) * 100

    # Convert results to DataFrame
    results_df = pd.DataFrame.from_dict(results, orient='index').reset_index()
    results_df.rename(columns={'index': 'team'}, inplace=True)

    # Merge with xG and xGA
    spi_df = df.merge(results_df[['team', 'SPI']], on='team')

    # Save results to CSV
    results_df.to_csv(f'{output_prefix}_results_detailed.csv', index=False)
    spi_df.to_csv(f'{output_prefix}_results_spi.csv', index=False)

    # Display the results
    print(f"Detailed Results for {output_prefix}:")
    print(results_df)
    print(f"\nSPI Results for {output_prefix}:")
    print(spi_df)

# Run simulation for each confederation
run_simulation('/home/albertovth/SPI/CONMEBOL.csv', 'CONMEBOL')
run_simulation('/home/albertovth/SPI/UEFA.csv', 'UEFA')
run_simulation('/home/albertovth/SPI/CONCACAF.csv', 'CONCACAF')

