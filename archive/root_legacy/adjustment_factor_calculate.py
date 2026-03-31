import pandas as pd

# Load the SPI data
spi_df = pd.read_csv('/home/albertovth/SPI/spi_final.csv')
spi_df = spi_df.rename(columns={'name': 'team'})

# Calculate the median SPI and 25th percentile SPI
median_spi = spi_df['spi'].median()
twenty_fifth_percentile_spi = spi_df['spi'].quantile(0.25)
max_spi = spi_df['spi'].max()
min_spi = spi_df['spi'].min()

print(f"Median SPI: {median_spi}")
print(f"25th Percentile SPI: {twenty_fifth_percentile_spi}")
print(f"Max SPI: {max_spi}")
print(f"Min SPI: {min_spi}")

# Function to calculate the adjustment factor
def calculate_adjustment_factor(max_spi, median_spi, twenty_fifth_percentile_spi, max_goal_limit=6):
    # Solve the equation: (adjustment_factor)*(max_spi/twenty_fifth_percentile_spi) - adjustment_factor*(median_spi/max_spi) <= max_goal_limit
    numerator = max_goal_limit
    denominator = (max_spi / twenty_fifth_percentile_spi) - (median_spi / max_spi)
    return numerator / denominator

# Calculate the required adjustment factor
adjustment_factor = calculate_adjustment_factor(max_spi, median_spi, twenty_fifth_percentile_spi, max_goal_limit=5.99)

print(f"Calculated adjustment factor: {adjustment_factor:.3f}")
