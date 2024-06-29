import pandas as pd

# Read individual CSVs
spi_conmebol = pd.read_csv('CONMEBOL_results_spi.csv')
spi_uefa = pd.read_csv('UEFA_results_spi.csv')
spi_concacaf = pd.read_csv('CONCACAF_results_spi.csv')

# Add confederation column
spi_conmebol['confed'] = 'CONMEBOL'
spi_uefa['confed'] = 'UEFA'
spi_concacaf['confed'] = 'CONCACAF'

# Read the dictionary CSV for name corrections
dictionary_df = pd.read_csv('/home/albertovth/SPI/dictionary.csv')
name_mapping = pd.Series(dictionary_df.corrected.values, index=dictionary_df.original).to_dict()

# Find the top xG, bottom xGA, and top SPI in each confederation
top_xg_conmebol = spi_conmebol['xG'].max()
bottom_xga_conmebol = spi_conmebol['xGA'].min()
top_spi_conmebol = spi_conmebol['SPI'].max()

top_xg_uefa = spi_uefa['xG'].max()
bottom_xga_uefa = spi_uefa['xGA'].min()
top_spi_uefa = spi_uefa['SPI'].max()

top_xg_concacaf = spi_concacaf['xG'].max()
bottom_xga_concacaf = spi_concacaf['xGA'].min()
top_spi_concacaf = spi_concacaf['SPI'].max()

# Scaling factors
scaling_factor_conmebol = 1.13
scaling_factor_uefa = 1.00
scaling_factor_concacaf = 0.79

# Scale top xG, bottom xGA, and top SPI
scaled_top_xg_conmebol = top_xg_uefa * scaling_factor_conmebol
scaled_bottom_xga_conmebol = bottom_xga_uefa / scaling_factor_conmebol

scaled_top_xg_uefa = top_xg_uefa * scaling_factor_uefa
scaled_bottom_xga_uefa = bottom_xga_uefa / scaling_factor_uefa

scaled_top_xg_concacaf = top_xg_uefa * scaling_factor_concacaf
scaled_bottom_xga_concacaf = bottom_xga_uefa / scaling_factor_concacaf

# Combine and rank
spi_combined = pd.concat([spi_conmebol, spi_uefa, spi_concacaf], ignore_index=True)

# Scale Off (xG) and Def (xGA)
spi_combined['off'] = spi_combined.apply(lambda row: row['xG'] / top_xg_uefa * scaled_top_xg_conmebol if row['confed'] == 'CONMEBOL' else row['xG'] / top_xg_uefa * scaled_top_xg_uefa if row['confed'] == 'UEFA' else row['xG'] / top_xg_uefa * scaled_top_xg_concacaf, axis=1)
spi_combined['def'] = spi_combined.apply(lambda row: row['xGA'] / bottom_xga_uefa * scaled_bottom_xga_conmebol if row['confed'] == 'CONMEBOL' else row['xGA'] / bottom_xga_uefa * scaled_bottom_xga_uefa if row['confed'] == 'UEFA' else row['xGA'] / bottom_xga_uefa * scaled_bottom_xga_concacaf, axis=1)

# Adjust SPIs by adding/subtracting median SPI
median_spi_uefa = spi_uefa['SPI'].median()

spi_combined['adjusted_spi'] = spi_combined.apply(
    lambda row: row['SPI'] + (4*scaling_factor_conmebol * median_spi_uefa - median_spi_uefa) if row['confed'] == 'CONMEBOL' else
    row['SPI'] + (4*scaling_factor_uefa * median_spi_uefa - median_spi_uefa) if row['confed'] == 'UEFA' else
    row['SPI'] + (4*scaling_factor_concacaf * median_spi_uefa - median_spi_uefa), axis=1
)

# Convert adjusted SPIs to percentiles and cap SPI at 99
spi_combined['spi_percentile'] = spi_combined['adjusted_spi'].rank(pct=True) * 100
spi_combined['spi'] = spi_combined['spi_percentile'].clip(upper=99)

# Apply name mapping
spi_combined['team'] = spi_combined['team'].map(name_mapping).fillna(spi_combined['team'])

# Rank teams
spi_combined['rank'] = spi_combined['spi'].rank(method='first', ascending=False).astype(int)
spi_combined = spi_combined.rename(columns={'team': 'name'})
spi_combined = spi_combined[['rank', 'name', 'confed', 'off', 'def', 'spi']]
spi_combined = spi_combined.sort_values(by=['spi', 'name'], ascending=[False, True])

# Save the final results
spi_combined.to_csv('/home/albertovth/SPI/spi_final.csv', index=False)

print("SPI Combined Results:")
print(spi_combined)

