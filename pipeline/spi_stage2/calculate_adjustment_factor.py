import pandas as pd
import numpy as np
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.paths import STAGE2_PRIOR_FILE

PRIOR_FILE = STAGE2_PRIOR_FILE
LOWER_STRENGTH = 0.05
UPPER_STRENGTH = 0.95
MAX_GOAL_LIMIT = 5.99

def add_strength(df, spi_col="spi", lower=LOWER_STRENGTH, upper=UPPER_STRENGTH):
    df = df.copy()
    n = len(df)
    if n <= 1:
        df["strength"] = 0.5
        return df
    ranks = df[spi_col].rank(method="average")
    pct = (ranks - 1) / (n - 1)  # 0..1
    df["strength"] = lower + (upper - lower) * pct
    return df

# Load the prior ranking and derive internal strength
spi_df = pd.read_csv(PRIOR_FILE)
spi_df = spi_df.rename(columns={'name': 'team'})
spi_df = add_strength(spi_df, spi_col="spi")

median_strength = spi_df['strength'].median()
max_strength = spi_df['strength'].max()
min_strength = spi_df['strength'].min()

print(f"Median strength: {median_strength}")
print(f"Max strength: {max_strength}")
print(f"Min strength: {min_strength}")

def calculate_adjustment_factor(max_strength, min_strength, max_goal_limit=MAX_GOAL_LIMIT):
    numerator = max_goal_limit
    denominator = (max_strength / min_strength) - 1
    return numerator / denominator

adjustment_factor = calculate_adjustment_factor(max_strength, min_strength, max_goal_limit=MAX_GOAL_LIMIT)
print(f"Calculated adjustment factor: {adjustment_factor:.3f}")

def calculate_adjusted_goals(home_score, away_score, home_strength, away_strength,
                             adjustment_factor, dynamism_variable, min_strength, max_strength):
    adjusted_home_goals = (
        home_score * adjustment_factor * (away_strength / (min_strength - dynamism_variable))
        - adjustment_factor * home_score * ((max_strength + dynamism_variable) / home_strength)
    )
    adjusted_away_goals = (
        away_score * adjustment_factor * (home_strength / (min_strength - dynamism_variable))
        - adjustment_factor * away_score * ((max_strength + dynamism_variable) / away_strength)
    )
    return adjusted_home_goals, adjusted_away_goals

optimal_dynamism = None
search_grid = np.arange(0.001, max(min_strength - 0.001, 0.001), 0.001)

for dynamism_variable in search_grid:
    adj_home_goals, adj_away_goals = calculate_adjusted_goals(
        home_score=1,
        away_score=1,
        home_strength=min_strength,
        away_strength=median_strength,
        adjustment_factor=adjustment_factor,
        dynamism_variable=dynamism_variable,
        min_strength=min_strength,
        max_strength=max_strength
    )

    print(
        f"Dynamism Variable: {dynamism_variable:.3f} | "
        f"Adjusted Home Goals: {adj_home_goals:.3f}, "
        f"Adjusted Away Goals: {adj_away_goals:.3f}"
    )

    if adj_home_goals > 0 and adj_away_goals > 0:
        optimal_dynamism = dynamism_variable
        print(f"Optimal Dynamism Variable found: {dynamism_variable:.3f}")
        break

if optimal_dynamism is None:
    print("No positive dynamism value found in the search range.")
