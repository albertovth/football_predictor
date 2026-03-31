#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python pipeline/spi_stage1/init_from_spi_538.py
python pipeline/spi_stage1/calculate_xg_xga.py
python pipeline/spi_stage1/simulate_spi.py
