import pandas as pd
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.paths import CONFEDS, SPI_FINAL_FILE, STAGE2_PRIOR_FILE

spi_538_df = pd.read_csv(STAGE2_PRIOR_FILE)

# Filter to include only CONMEBOL, UEFA, CONCACAF, AFC, CAF and OFC teams
spi_538_df = spi_538_df[spi_538_df['confed'].isin(CONFEDS)]

# Select and rename relevant columns
spi_538_df = spi_538_df[['name', 'confed', 'off', 'def', 'spi']]
spi_538_df = spi_538_df.rename(columns={'name': 'team'})

# Save it as the initial spi_final.csv
SPI_FINAL_FILE.parent.mkdir(parents=True, exist_ok=True)
spi_538_df.to_csv(SPI_FINAL_FILE, index=False)

print("SPI data from May 26, 2025 saved as initial spi_final.csv")
