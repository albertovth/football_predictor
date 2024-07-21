import pandas as pd

# Load the SPI data from the May 25, 2021 snapshot
file_path = '/home/albertovth/SPI/spi_global_rankings_intl_25_5_2021.csv'
spi_538_df = pd.read_csv(file_path)

# Filter to include only CONMEBOL, UEFA, CONCACAF, AFC, CAF and OFC teams
confederations = ['CONMEBOL', 'UEFA', 'CONCACAF','AFC','CAF','OFC']
spi_538_df = spi_538_df[spi_538_df['confed'].isin(confederations)]

# Select and rename relevant columns
spi_538_df = spi_538_df[['name', 'confed', 'off', 'def', 'spi']]
spi_538_df = spi_538_df.rename(columns={'name': 'team'})

# Save it as the initial spi_final.csv
spi_538_df.to_csv('/home/albertovth/SPI/spi_final.csv', index=False)

print("SPI data from May 25, 2021 saved as initial spi_final.csv")
