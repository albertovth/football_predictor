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

# Combine data
spi_combined = pd.concat([spi_conmebol, spi_uefa, spi_concacaf], ignore_index=True)

# Normalize Off (xG) and Def (xGA) values
spi_combined['off'] = spi_combined['xG']
spi_combined['def'] = spi_combined['xGA']

# Use the SPI directly without additional competitiveness scaling
spi_combined['spi'] = spi_combined['SPI']
spi_combined['spi'] = spi_combined['spi'].clip(upper=99)

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
