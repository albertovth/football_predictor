import pandas as pd

# Load the 538 SPI data
url = "https://projects.fivethirtyeight.com/soccer-api/international/spi_global_rankings_intl.csv"
spi_538_df = pd.read_csv(url)

# Filter to include only CONMEBOL, UEFA, CONCACAF, AFC, CAF and OFC teams
confederations = ['CONMEBOL', 'UEFA', 'CONCACAF','AFC','CAF','OFC']
spi_538_df = spi_538_df[spi_538_df['confed'].isin(confederations)]

# Select and rename relevant columns
spi_538_df = spi_538_df[['name', 'confed', 'off', 'def', 'spi']]
spi_538_df = spi_538_df.rename(columns={'name': 'team'})

# Save it as the initial spi_final.csv
spi_538_df.to_csv('/home/albertovth/SPI/spi_final.csv', index=False)

print("538 SPI data saved as initial spi_final.csv")
