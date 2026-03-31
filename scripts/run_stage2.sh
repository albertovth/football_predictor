#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python pipeline/spi_stage2/init_from_spi_538.py
python pipeline/spi_stage2/calculate_adjustment_factor.py
python pipeline/spi_stage2/calculate_caps_off_def.py
python pipeline/spi_stage2/calculate_low_team_cutoff.py
python pipeline/spi_stage2/calculate_xg_xga.py
python pipeline/spi_stage2/simulate_spi.py
