# Football Predictor

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://footballpredictor.streamlit.app)

`/home/albertovth/football_predictor` is now the canonical codebase for this project.

The older `/home/albertovth/SPI` workspace is no longer the source of truth. Relevant stage 1 and stage 2 code, configuration, and generated data needed for the current workflow have been migrated into this repository. Legacy scripts from the old flat layout have been preserved under `archive/root_legacy/` only for reference.

## Repository Structure

```text
football_predictor/
├── app/                      # Streamlit application implementation
├── src/football_predictor/   # Shared Python helpers and path configuration
├── pipeline/
│   ├── spi_stage1/           # Stage 1 ranking pipeline
│   └── spi_stage2/           # Stage 2 ranking pipeline
├── scripts/                  # Wrapper scripts for common workflows
├── data/
│   ├── config/               # Dictionary, confederations, prior rankings
│   ├── intermediate/         # Working files produced by the pipeline
│   └── output/               # Final ranking artifacts
├── archive/root_legacy/      # Archived pre-reorg root scripts
├── football_predictor.py     # Root compatibility wrapper for Streamlit
└── ranking_final.csv         # Root copy used by the app and GitHub consumers
```

## Current Layout

### `app/`

Contains the actual Streamlit app implementation in `app/football_predictor.py`.

### `src/football_predictor/`

Contains shared repository helpers.

- `src/football_predictor/paths.py`
  Central path definition module used by the pipeline scripts so they run relative to the repository instead of `/home/albertovth/SPI`.
- `src/football_predictor/stage_config.py`
  Shared stage window and parameter-estimation helper used to resolve stage dates and re-estimate stage-specific `adjustment factor`, `dynamism variable`, and `cutoff`.

### `pipeline/`

Contains the active ranking pipeline:

- `pipeline/spi_stage1/`
  Builds the stage 1 prior and updated confederation-level xG/xGA data. By default it uses the 2021-05-26 to 2025-05-26 window, but the stage window and cutoff quantile can now be overridden from the terminal.
- `pipeline/spi_stage2/`
  Uses the stage 2 prior and corrected balanced low-team logic to build the latest ranking outputs and final `ranking_final.csv`. By default it uses the 2025-05-27 to today window, but the stage window and cutoff quantile can now be overridden from the terminal.

### `scripts/`

Contains executable wrappers:

- `scripts/run_stage1.sh`
- `scripts/run_stage2.sh`
- `scripts/update_rankings.sh`

### `data/`

Contains inputs and outputs used by the active code:

- `data/config/`
  Static configuration and prior ranking CSVs.
- `data/intermediate/`
  Working files such as `spi_final.csv`, `aggregated_xg_data.csv`, `opponent_strength_data.csv`, and confederation split CSVs.
- `data/output/`
  Final output files, including `data/output/ranking_final.csv`.

### `archive/root_legacy/`

Contains the older flat root-level scripts that were previously at repo root. These are not the active code path and should not be used for current documentation or operational instructions.

## Relationship To The Old SPI Workspace

Before this reorganization, active work was split between:

- the GitHub repository clone in `/home/albertovth/football_predictor`
- the newer experimental and production scripts in `/home/albertovth/SPI`

That split has been collapsed into this repository. The repo now contains:

- the canonical Streamlit app
- the migrated stage 1 pipeline
- the migrated stage 2 pipeline
- the needed configuration and prior data files
- the generated ranking outputs used by the app

The old `/home/albertovth/SPI` directory can still be useful as a historical reference, but updates should now be made in this repository first.

## Ranking File Contract

The final rankings are produced at:

- `data/output/ranking_final.csv`

For compatibility with the existing app and external consumers, the stage 2 simulation also copies the same result to:

- `ranking_final.csv`

The Streamlit app reads the root `ranking_final.csv`. This preserves the previous public contract while allowing the pipeline to use a cleaner internal structure.

## Root Streamlit Wrapper

The repo keeps a root-level `football_predictor.py` for compatibility.

That file is now a thin wrapper which executes:

- `app/football_predictor.py`

This preserves the existing Streamlit entrypoint:

```bash
streamlit run football_predictor.py
```

while allowing the real app implementation to live under `app/`.

## Running The Project

From the repository root:

Activate the intended environment first:

```bash
cd /home/albertovth/football_predictor
source ~/.bashrc >/dev/null 2>&1 || true
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate spyder607
```

### Run Stage 1

```bash
bash scripts/run_stage1.sh
```

### Run Stage 2

```bash
bash scripts/run_stage2.sh
```

### Run Stage 1 And Stage 2 Sequentially

```bash
bash scripts/update_rankings.sh
```

### Run The Streamlit App

```bash
streamlit run football_predictor.py
```

## Stage Window Configuration

The pipeline now supports terminal-driven stage windows and structural cutoff overrides through environment variables.

Default stage windows:

- Stage 1: `2021-05-26` to `2025-05-26`
- Stage 2: `2025-05-27` to `today`

Supported overrides:

- `STAGE1_START_DATE`
- `STAGE1_END_DATE`
- `STAGE1_CUTOFF_QUANTILE`
- `STAGE2_START_DATE`
- `STAGE2_END_DATE`
- `STAGE2_CUTOFF_QUANTILE`

Examples:

```bash
STAGE1_END_DATE=2025-06-30 bash scripts/run_stage1.sh
STAGE2_END_DATE=2026-06-30 bash scripts/run_stage2.sh
STAGE2_START_DATE=2026-04-01 STAGE2_END_DATE=2026-08-31 bash scripts/run_stage2.sh
```

Stage-specific structure remains unchanged:

- stage 1 estimates in raw `spi` space
- stage 2 estimates in `strength` space
- `adjustment factor`, `dynamism variable`, and `cutoff` are re-estimated from the active stage universe before the main calculation

## Pipeline Summary

The active workflow is:

1. Initialize the stage prior from the configured FiveThirtyEight snapshot.
2. Re-estimate the active stage `adjustment factor`, `dynamism variable`, and `cutoff`.
3. Calculate adjusted xG/xGA metrics from match results.
4. Write confederation-level intermediate files under `data/intermediate/confed/`.
5. Run the confederation simulation step.
6. Produce the final ranking table in `data/output/ranking_final.csv`.
7. Copy the same final ranking to the root `ranking_final.csv` for app compatibility.

## Data Sources And Attribution

### Match Results

Updated match results are read from Martj42's public international results dataset:

- Repository: <https://github.com/martj42/international_results>
- License: CC0 1.0
- Data file: <https://raw.githubusercontent.com/martj42/international_results/master/results.csv>

### Initial Ranking Structure

The initial ranking structure and priors are derived from FiveThirtyEight's Soccer Power Index data:

- Documentation: <https://github.com/fivethirtyeight/data/blob/master/soccer-spi/README.md>
- License: CC-BY-4.0

### Logos And Flags

The Streamlit app uses Wikipedia-hosted team logos and flags:

- Source: <https://www.wikipedia.org>
- License family: Creative Commons Attribution-ShareAlike

## Notes

- The root `README.md` and `METHODS.md` describe the active reorganized repository.
- `docs/README.md` and `docs/METHODS.md` currently mirror the root documents.
- Archived legacy scripts may still contain historical `/home/albertovth/SPI` path references, but active code no longer depends on them.
- The all-versus-all simulation is now much faster because the active simulation scripts use NumPy Poisson sampling instead of the older manual inverse-Poisson path.
