import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_path(name: str, default: Path) -> Path:
    """Resolve an optional run-specific path without changing production defaults."""
    return Path(os.getenv(name, str(default))).expanduser().resolve()


DATA_DIR = _env_path("FOOTBALL_DATA_DIR", REPO_ROOT / "data")
CONFIG_DIR = DATA_DIR / "config"
PRIORS_DIR = CONFIG_DIR / "priors"
INTERMEDIATE_DIR = _env_path("FOOTBALL_INTERMEDIATE_DIR", DATA_DIR / "intermediate")
CONFED_DIR = INTERMEDIATE_DIR / "confed"
OUTPUT_DIR = _env_path("FOOTBALL_OUTPUT_DIR", DATA_DIR / "output")

DICTIONARY_FILE = CONFIG_DIR / "dictionary.csv"
CONFEDERATIONS_FILE = CONFIG_DIR / "confederations.csv"

STAGE1_PRIOR_FILE = _env_path(
    "FOOTBALL_STAGE1_PRIOR_FILE",
    PRIORS_DIR / "spi_global_rankings_intl_25_5_2021.csv",
)
STAGE2_PRIOR_FILE = _env_path(
    "FOOTBALL_STAGE2_PRIOR_FILE",
    PRIORS_DIR / "spi_global_rankings_intl_26_5_2025.csv",
)

SPI_FINAL_FILE = INTERMEDIATE_DIR / "spi_final.csv"
AGGREGATED_XG_FILE = INTERMEDIATE_DIR / "aggregated_xg_data.csv"
OPPONENT_SPI_FILE = INTERMEDIATE_DIR / "opponent_spi_data.csv"
OPPONENT_STRENGTH_FILE = INTERMEDIATE_DIR / "opponent_strength_data.csv"

RANKING_OUTPUT_FILE = _env_path(
    "FOOTBALL_RANKING_OUTPUT_FILE",
    OUTPUT_DIR / "ranking_final.csv",
)
ROOT_RANKING_FILE = _env_path(
    "FOOTBALL_ROOT_RANKING_FILE",
    REPO_ROOT / "ranking_final.csv",
)

APP_ENTRYPOINT = REPO_ROOT / "app" / "football_predictor.py"

CONFEDS = ["CONMEBOL", "UEFA", "CONCACAF", "AFC", "CAF", "OFC"]
CONFED_FILES = {confed: CONFED_DIR / f"{confed}.csv" for confed in CONFEDS}

STAGE1_END_DATE = "2025-05-26"
RESULTS_URL = os.getenv(
    "FOOTBALL_RESULTS_SOURCE",
    "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
)
GOAL_MEDIAN_RESULTS_SOURCE = os.getenv(
    "FOOTBALL_GOAL_MEDIAN_RESULTS_SOURCE",
    RESULTS_URL,
)
