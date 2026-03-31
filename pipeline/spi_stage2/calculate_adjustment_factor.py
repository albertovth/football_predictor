import pandas as pd
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from football_predictor.paths import STAGE2_PRIOR_FILE
from football_predictor.stage_config import add_strength, estimate_adjustment_factor, estimate_dynamism_variable

PRIOR_FILE = STAGE2_PRIOR_FILE
LOWER_STRENGTH = 0.05
UPPER_STRENGTH = 0.95
MAX_GOAL_LIMIT = 5.99

# Load the prior ranking and derive internal strength
spi_df = pd.read_csv(PRIOR_FILE)
spi_df = spi_df.rename(columns={'name': 'team'})
spi_df = add_strength(spi_df, spi_col="spi", lower=LOWER_STRENGTH, upper=UPPER_STRENGTH)

median_strength = spi_df['strength'].median()
max_strength = spi_df['strength'].max()
min_strength = spi_df['strength'].min()

print(f"Median strength: {median_strength}")
print(f"Max strength: {max_strength}")
print(f"Min strength: {min_strength}")

adjustment_factor = estimate_adjustment_factor(max_strength, min_strength, max_goal_limit=MAX_GOAL_LIMIT)
print(f"Calculated adjustment factor: {adjustment_factor:.3f}")
optimal_dynamism = estimate_dynamism_variable(
    stage_name="stage2",
    metric_min=min_strength,
    metric_median=median_strength,
    metric_max=max_strength,
    adjustment_factor=adjustment_factor,
)
print(f"Optimal Dynamism Variable found: {optimal_dynamism:.3f}")
