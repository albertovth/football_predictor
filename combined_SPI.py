
import pandas as pd

# Read individual CSVs
spi_conmebol = pd.read_csv('CONMEBOL_results_spi.csv')
spi_uefa = pd.read_csv('UEFA_results_spi.csv')
spi_concacaf = pd.read_csv('CONCACAF_results_spi.csv')

# Add confederation column
spi_conmebol['confed'] = 'CONMEBOL'
spi_uefa['confed'] = 'UEFA'
spi_concacaf['confed'] = 'CONCACAF'

# Function to calculate relative xG and xGA
def calculate_relative_xg(spi_df):
    top_value = spi_df['xG'].max()
    spi_df['relative_xg'] = spi_df['xG'] / top_value
    return spi_df, top_value

def calculate_relative_xga(spi_df):
    bottom_value = spi_df['xGA'].min()  # For xGA, lower is better
    spi_df['relative_xga'] = spi_df['xGA'] / bottom_value  # Relative for xGA
    return spi_df, bottom_value

# Calculate relative xG and xGA
spi_conmebol, top_xg_conmebol = calculate_relative_xg(spi_conmebol)
spi_conmebol, bottom_xga_conmebol = calculate_relative_xga(spi_conmebol)
spi_uefa, top_xg_uefa = calculate_relative_xg(spi_uefa)
spi_uefa, bottom_xga_uefa = calculate_relative_xga(spi_uefa)
spi_concacaf, top_xg_concacaf = calculate_relative_xg(spi_concacaf)
spi_concacaf, bottom_xga_concacaf = calculate_relative_xga(spi_concacaf)

# Scale top xG and xGA using hierarchical scaling factors
top_xg_conmebol_scaled = top_xg_uefa * 1.13
top_xg_concacaf_scaled = top_xg_uefa * 0.79
bottom_xga_conmebol_scaled = bottom_xga_uefa / 1.13
bottom_xga_concacaf_scaled = bottom_xga_uefa / 0.79

# Recalculate xG and xGA based on the new top values
spi_conmebol['scaled_xg'] = spi_conmebol['relative_xg'] * top_xg_conmebol_scaled
spi_uefa['scaled_xg'] = spi_uefa['relative_xg'] * top_xg_uefa
spi_concacaf['scaled_xg'] = spi_concacaf['relative_xg'] * top_xg_concacaf_scaled

spi_conmebol['scaled_xga'] = spi_conmebol['relative_xga'] * bottom_xga_conmebol_scaled
spi_uefa['scaled_xga'] = spi_uefa['relative_xga'] * bottom_xga_uefa
spi_concacaf['scaled_xga'] = spi_concacaf['relative_xga'] * bottom_xga_concacaf_scaled

# Function to calculate relative SPIs
def calculate_relative_spis(spi_df):
    top_spi = spi_df['SPI'].max()
    spi_df['relative_spi'] = spi_df['SPI'] / top_spi
    return spi_df, top_spi

# Calculate relative SPIs
spi_conmebol, top_spi_conmebol = calculate_relative_spis(spi_conmebol)
spi_uefa, top_spi_uefa = calculate_relative_spis(spi_uefa)
spi_concacaf, top_spi_concacaf = calculate_relative_spis(spi_concacaf)

# Scale top SPIs using hierarchical scaling factors
top_spi_conmebol_scaled = top_spi_uefa * 1.13
top_spi_concacaf_scaled = top_spi_uefa * 0.79

# Recalculate SPIs based on the new top SPIs
spi_conmebol['scaled_spi'] = spi_conmebol['relative_spi'] * top_spi_conmebol_scaled
spi_uefa['scaled_spi'] = spi_uefa['relative_spi'] * top_spi_uefa
spi_concacaf['scaled_spi'] = spi_concacaf['relative_spi'] * top_spi_concacaf_scaled

# Combine results
spi_combined = pd.concat([spi_uefa, spi_conmebol, spi_concacaf], ignore_index=True)

# Create spi_final.csv with the required columns and format
spi_combined['rank'] = spi_combined['scaled_spi'].rank(method='first', ascending=False).astype(int)
spi_combined = spi_combined.rename(columns={'team': 'name', 'scaled_xg': 'off', 'scaled_xga': 'def', 'scaled_spi': 'spi'})
spi_combined = spi_combined[['rank', 'name', 'confed', 'off', 'def', 'spi']]
spi_combined = spi_combined.sort_values(by=['spi', 'name'], ascending=[False, True])

# Save the final results
spi_combined.to_csv('spi_final.csv', index=False)

print("SPI Combined Results:")
print(spi_combined)