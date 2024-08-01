import pandas as pd
import numpy as np  # Import numpy as np

# Load the SPI data
spi_df = pd.read_csv('/home/albertovth/SPI/spi_final.csv')
spi_df = spi_df.rename(columns={'name': 'team'})

# Calculate the median SPI, 25th percentile SPI, max SPI, and min SPI
median_spi = spi_df['spi'].median()
twenty_fifth_percentile_spi = spi_df['spi'].quantile(0.25)
max_spi = spi_df['spi'].max()
min_spi = spi_df['spi'].min()

print(f"Median SPI: {median_spi}")
print(f"25th Percentile SPI: {twenty_fifth_percentile_spi}")
print(f"Max SPI: {max_spi}")
print(f"Min SPI: {min_spi}")

# Function to calculate the adjustment factor
def calculate_adjustment_factor(max_spi, min_spi, max_goal_limit=6):
    # Solve the equation: (adjustment_factor)*(max_spi/min_spi - 1) <= max_goal_limit
    numerator = max_goal_limit
    denominator = (max_spi / min_spi) - 1
    return numerator / denominator

# Calculate the required adjustment factor
adjustment_factor = calculate_adjustment_factor(max_spi, min_spi, max_goal_limit=5.99)

print(f"Calculated adjustment factor: {adjustment_factor:.3f}")

# Function to calculate goals with a dynamism variable
def calculate_adjusted_goals(row, adjustment_factor, dynamism_variable, min_spi, max_spi, median_spi):
    home_team_spi = row['home_team_spi']
    away_team_spi = row['away_team_spi']

    adjusted_home_goals = (
        row['home_score'] * adjustment_factor * (away_team_spi / (min_spi - dynamism_variable))
        - adjustment_factor * row['home_score'] * ((max_spi + dynamism_variable) / home_team_spi)
    )
    adjusted_away_goals = (
        row['away_score'] * adjustment_factor * (home_team_spi / (min_spi - dynamism_variable))
        - adjustment_factor * row['away_score'] * ((max_spi + dynamism_variable) / away_team_spi)
    )

    return adjusted_home_goals, adjusted_away_goals

# Iterate over a range of dynamism variables to find the optimal one
for dynamism_variable in np.arange(0.01, 0.5, 0.01):
    test_row = {'home_score': 1, 'away_score': 1, 'home_team_spi': min_spi, 'away_team_spi': median_spi}

    adj_home_goals, adj_away_goals = calculate_adjusted_goals(
        test_row, adjustment_factor, dynamism_variable, min_spi, max_spi, median_spi
    )

    print(f"Dynamism Variable: {dynamism_variable:.2f} | Adjusted Home Goals: {adj_home_goals:.3f}, Adjusted Away Goals: {adj_away_goals:.3f}")

    if adj_home_goals > 0 and adj_away_goals > 0:
        print(f"Optimal Dynamism Variable found: {dynamism_variable:.2f}")
        break
