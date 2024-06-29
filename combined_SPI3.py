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

# Adjust SPI based on competitiveness
median_spi_conmebol = spi_conmebol['SPI'].median()
median_spi_concacaf = spi_concacaf['SPI'].median()
median_spi_uefa = spi_uefa['SPI'].quantile(0.5)


def adjust_spi(row, median_spi_conmebol, median_spi_concacaf, competitiveness_factor_conmebol=1.13, competitiveness_factor_uefa=1, competitiveness_factor_concacaf=0.79):
    if row['confed'] == 'CONMEBOL':
        return min(row['SPI']*competitiveness_factor_conmebol,99)
    elif row['confed'] == 'UEFA':
        return min(row['SPI']*competitiveness_factor_uefa,99)
    elif row['confed'] == 'CONCACAF':
        return min(row['SPI']*competitiveness_factor_concacaf,99)
    else:
        return row['SPI']

def adjust_conmebol(row, median_spi_conmebol):
    if row['confed'] == 'CONMEBOL' and row['SPI'] < median_spi_conmebol:
        return min(row['SPI'] + median_spi_conmebol, 99)
    else:
        return row['SPI']

def adjust_uefa(row):
    if row['confed'] == 'UEFA' and row['SPI']:
        return min(row['SPI'] + median_spi_uefa/3, 99)
    else:
        return row['SPI']



spi_combined['SPI'] = spi_combined.apply(lambda row: adjust_spi(row, median_spi_conmebol, median_spi_concacaf), axis=1)

spi_combined['SPI'] = spi_combined.apply(lambda row: adjust_conmebol(row, median_spi_conmebol), axis=1)

spi_combined['SPI'] = spi_combined.apply(lambda row: adjust_uefa(row), axis=1)


# Clip SPI values at 99
spi_combined['SPI'] = spi_combined['SPI'].clip(upper=99)

# Apply name mapping
spi_combined['team'] = spi_combined['team'].map(name_mapping).fillna(spi_combined['team'])

# Calculate median of actual goals scored and conceded
match_data = pd.read_csv("https://raw.githubusercontent.com/martj42/international_results/master/results.csv")
match_data['date'] = pd.to_datetime(match_data['date'])
match_data = match_data[match_data['date'] >= '2020-01-01']  # Adjust the date range as needed
median_actual_goals_scored = match_data[['home_score', 'away_score']].stack().median()
median_actual_goals_conceded = match_data[['home_score', 'away_score']].stack().median()

# Scale xG and xGA values
xg_median = spi_combined['xG'].median()
xga_median = spi_combined['xGA'].median()

spi_combined['xG'] = spi_combined['xG'] * (median_actual_goals_scored / xg_median)
spi_combined['xGA'] = spi_combined['xGA'] * (median_actual_goals_conceded / xga_median)

# Normalize Off (xG) and Def (xGA) values again after scaling
spi_combined['off'] = spi_combined['xG']
spi_combined['def'] = spi_combined['xGA']

# Rank teams
spi_combined['rank'] = spi_combined['SPI'].rank(method='first', ascending=False).astype(int)
spi_combined = spi_combined.rename(columns={'team': 'name'})
spi_combined = spi_combined[['rank', 'name', 'confed', 'off', 'def', 'SPI']]
spi_combined = spi_combined.sort_values(by=['SPI', 'name'], ascending=[False, True])

# Save the final results
spi_combined.to_csv('/home/albertovth/SPI/spi_final.csv', index=False)

print("SPI Combined Results:")
print(spi_combined)

