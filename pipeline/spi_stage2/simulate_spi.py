import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import shutil
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.paths import (
    CONFEDS,
    CONFED_FILES,
    DICTIONARY_FILE,
    GOAL_MEDIAN_RESULTS_SOURCE,
    RANKING_OUTPUT_FILE,
    ROOT_RANKING_FILE,
)
from football_predictor.stage_config import (
    empirical_median_goals,
    resolve_goal_median_window,
    resolve_stage_window,
)

start_date, end_date = resolve_stage_window("stage2")
goal_median_start, goal_median_end = resolve_goal_median_window(start_date, end_date)
median_goals = empirical_median_goals(
    GOAL_MEDIAN_RESULTS_SOURCE,
    goal_median_start,
    goal_median_end,
)

print(f"Empirical median goals (used as baseline): {median_goals}")
print(
    "Empirical goal-median window: "
    f"{goal_median_start.date()} to {goal_median_end.date()}"
)
print(f"Stage 2 simulation window: {start_date.date()} to {end_date.date()}")


def run_simulation(df):
    n_simulations = 10000
    results = {team: {'wins': 0, 'draws': 0, 'losses': 0} for team in df['team']}

    for i, team_a_row in tqdm(df.iterrows(), total=len(df), desc="Teams progress"):
        for j, team_b_row in tqdm(df.iterrows(), total=len(df), desc="Match progress", leave=False):
            if i != j:
                team_a = team_a_row['team']
                team_b = team_b_row['team']

                expected_goals_team_a = (team_a_row['xG'] + team_b_row['xGA']) / 2
                expected_goals_team_b = (team_b_row['xG'] + team_a_row['xGA']) / 2

                goals_team_a = np.random.poisson(expected_goals_team_a, size=n_simulations)
                goals_team_b = np.random.poisson(expected_goals_team_b, size=n_simulations)

                wins_team_a = np.sum(goals_team_a > goals_team_b)
                draws = np.sum(goals_team_a == goals_team_b)
                wins_team_b = np.sum(goals_team_a < goals_team_b)

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
    # Load and label individual CSVs
    dfs = [pd.read_csv(path) for path in file_paths]
    for df, conf in zip(dfs, CONFEDS):
        df['confed'] = conf
    combined_df = pd.concat(dfs, ignore_index=True)
    
    combined_df=combined_df[combined_df['team']!='Russia']

    results = run_simulation(combined_df)
    results_df = pd.DataFrame.from_dict(results, orient='index').reset_index()
    results_df.rename(columns={'index': 'team'}, inplace=True)

    # Merge SPI results back into full dataset
    spi_df = combined_df.merge(results_df[['team', 'spi']], on='team')
    spi_df['off'] = spi_df['xG']
    spi_df['def'] = spi_df['xGA']

    # Apply name corrections
    dictionary_df = pd.read_csv(DICTIONARY_FILE)
    name_mapping = pd.Series(dictionary_df.corrected.values, index=dictionary_df.original).to_dict()
    spi_df['team'] = spi_df['team'].map(name_mapping).fillna(spi_df['team'])

    # Rank and save final SPI table
    spi_df['rank'] = spi_df['spi'].rank(method='first', ascending=False).astype(int)
    spi_df = spi_df.rename(columns={'team': 'name'})
    spi_df = spi_df[['rank', 'name', 'confed', 'off', 'def', 'spi']].sort_values(by=['spi', 'name'], ascending=[False, True])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    spi_df.to_csv(output_file, index=False)
    shutil.copyfile(output_file, ROOT_RANKING_FILE)
    print("SPI Combined Results:")
    print(spi_df)

if __name__ == "__main__":
    run_combined_simulation(
        [CONFED_FILES[confed] for confed in CONFEDS],
        RANKING_OUTPUT_FILE,
    )
