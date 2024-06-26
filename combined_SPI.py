import pandas as pd
from datetime import datetime, timedelta

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

spi_conmebol['scaled_spi'] = spi_conmebol['scaled_spi'].clip(upper=99)
spi_uefa['scaled_spi'] = spi_uefa['scaled_spi'].clip(upper=99)
spi_concacaf['scaled_spi'] = spi_concacaf['scaled_spi'].clip(upper=99)

# Combine results
spi_combined = pd.concat([spi_uefa, spi_conmebol, spi_concacaf], ignore_index=True)

# Load the original match data to calculate actual xG and xGA
url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
df = pd.read_csv(url)

# Filter data for the last four years
today = datetime.today()
four_years_ago = today - timedelta(days=4*365)
df['date'] = pd.to_datetime(df['date'])
filtered_df = df[df['date'] >= four_years_ago]

# Calculate actual xG and xGA
actual_xg_data = []

for index, row in filtered_df.iterrows():
    home_team = row['home_team']
    away_team = row['away_team']
    home_goals = row['home_score']
    away_goals = row['away_score']

    actual_xg_data.append({'team': home_team, 'xG': home_goals, 'xGA': away_goals})
    actual_xg_data.append({'team': away_team, 'xG': away_goals, 'xGA': home_goals})

actual_xg_df = pd.DataFrame(actual_xg_data)

# Aggregate data to get actual average xG and xGA per team
actual_aggregated_data = actual_xg_df.groupby('team').agg({
    'xG': 'mean',
    'xGA': 'mean'
}).reset_index()

# Merge with SPI combined to filter out only the relevant teams
actual_aggregated_data = actual_aggregated_data.merge(spi_combined[['team']], on='team')

# Find the top Off (scaled_xg) and bottom Def (scaled_xga) team from UEFA
top_off_team = spi_combined[spi_combined['confed'] == 'UEFA'].sort_values(by='scaled_xg', ascending=False).iloc[0]
bottom_def_team = spi_combined[spi_combined['confed'] == 'UEFA'].sort_values(by='scaled_xga', ascending=True).iloc[0]

# Get the actual xG and xGA for the top Off team and bottom Def team
actual_top_xg = actual_aggregated_data[actual_aggregated_data['team'] == top_off_team['team']]['xG'].values[0]
actual_bottom_xga = actual_aggregated_data[actual_aggregated_data['team'] == bottom_def_team['team']]['xGA'].values[0]

# Scale Off (scaled_xg) and Def (scaled_xga) based on the actual xG and xGA
spi_combined['off'] = spi_combined['scaled_xg'] / top_off_team['scaled_xg'] * actual_top_xg
spi_combined['def'] = spi_combined['scaled_xga'] / bottom_def_team['scaled_xga'] * actual_bottom_xga

# Cap Off and Def at 10
spi_combined['off'] = spi_combined['off'].clip(upper=10)
spi_combined['def'] = spi_combined['def'].clip(upper=10)

# Correct the team names using the mapping dictionary
spi_combined['team'] = spi_combined['team'].map(name_mapping).fillna(spi_combined['team'])

# Create spi_final.csv with the required columns and format
spi_combined['rank'] = spi_combined['scaled_spi'].rank(method='first', ascending=False).astype(int)
spi_combined = spi_combined.rename(columns={'team': 'name', 'scaled_spi': 'spi'})
spi_combined = spi_combined[['rank', 'name', 'confed', 'off', 'def', 'spi']]
spi_combined = spi_combined.sort_values(by=['spi', 'name'], ascending=[False, True])

# Save the final results
spi_combined.to_csv('/home/albertovth/SPI/spi_final.csv', index=False)

print("SPI Combined Results:")
print(spi_combined)
