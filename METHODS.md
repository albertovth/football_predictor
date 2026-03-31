# Methods

This document describes the active methodology implemented in the reorganized repository at `/home/albertovth/football_predictor`.

It is aligned with the current code under:

- `app/`
- `src/football_predictor/`
- `pipeline/spi_stage1/`
- `pipeline/spi_stage2/`
- `scripts/`
- `data/`

It does not describe the archived legacy scripts under `archive/root_legacy/`.

## Canonical Codebase

`/home/albertovth/football_predictor` is now the canonical codebase for both ranking generation and the Streamlit app.

Historically, updated work had accumulated in `/home/albertovth/SPI`, especially the newer stage 1 and stage 2 scripts. Those operational pieces have now been migrated into this repository, and the active pipeline has been refactored to use repository-relative paths via `src/football_predictor/paths.py`.

## Method Overview

The project updates football team ratings in two broad phases:

1. Derive offensive and defensive metrics from match history.
2. Simulate all-versus-all matchups from those metrics to derive a ranking table.

The repository currently keeps two explicit pipeline stages:

- `pipeline/spi_stage1/`
- `pipeline/spi_stage2/`

Stage 1 produces an updated ranking snapshot that becomes the stage 2 prior. Stage 2 then applies the current corrected and balanced methodology to produce the latest final ranking used by the app.

## Repository Roles In The Method

### `pipeline/spi_stage1/`

Stage 1 contains:

- `init_from_spi_538.py`
- `calculate_xg_xga.py`
- `simulate_spi.py`

This stage:

- starts from the 2021-05-25 prior snapshot in `data/config/priors/spi_global_rankings_intl_25_5_2021.csv`
- filters to the six supported confederations
- initializes `data/intermediate/spi_final.csv`
- by default uses historical results from 2021-05-26 through 2025-05-26
- resolves the active stage window through `src/football_predictor/stage_config.py`
- re-estimates `adjustment factor`, `dynamism variable`, and `cutoff` in raw `spi` space before the main xG/xGA calculation
- computes confederation-level xG/xGA files
- simulates the all-versus-all ranking table
- writes the stage 1 resulting ranking to `data/config/priors/spi_global_rankings_intl_26_5_2025.csv`

### `pipeline/spi_stage2/`

Stage 2 contains:

- `init_from_spi_538.py`
- `calculate_adjustment_factor.py`
- `calculate_caps_off_def.py`
- `calculate_low_team_cutoff.py`
- `calculate_xg_xga.py`
- `simulate_spi.py`

This stage:

- starts from the stage 2 prior in `data/config/priors/spi_global_rankings_intl_26_5_2025.csv`
- reinitializes `data/intermediate/spi_final.csv`
- by default uses historical results from 2025-05-27 through today
- resolves the active stage window through `src/football_predictor/stage_config.py`
- converts the prior into internal `strength` values
- re-estimates `adjustment factor`, `dynamism variable`, and `cutoff` in `strength` space before the main xG/xGA calculation
- uses the corrected balanced low-team methodology
- generates fresh intermediate xG/xGA and confederation split files
- simulates the final ranking table
- writes `data/output/ranking_final.csv`
- copies the same file to root `ranking_final.csv` for app compatibility

## Input Data

### Prior Rankings

The current pipeline uses two prior files:

- `data/config/priors/spi_global_rankings_intl_25_5_2021.csv`
- `data/config/priors/spi_global_rankings_intl_26_5_2025.csv`

### Team Name Mapping

The pipeline uses:

- `data/config/dictionary.csv`

This file maps between naming variants so that:

- historical results
- confederation metadata
- priors
- output rankings

can be aligned consistently.

### Confederation Mapping

The pipeline uses:

- `data/config/confederations.csv`

This file is used to assign teams to:

- CONMEBOL
- UEFA
- CONCACAF
- AFC
- CAF
- OFC

## Match Data

Both stages use:

- <https://raw.githubusercontent.com/martj42/international_results/master/results.csv>

The historical results are filtered by date window depending on stage. Those stage windows are now configurable at runtime.

Friendly matches are down-weighted by halving the recorded goals before metric generation.

## Stage Window And Structural Parameter Configuration

The active code uses `src/football_predictor/stage_config.py` to resolve stage windows and structural parameter inputs.

Default windows:

- stage 1: `2021-05-26` to `2025-05-26`
- stage 2: `2025-05-27` to `today`

Supported environment-variable overrides:

- `STAGE1_START_DATE`
- `STAGE1_END_DATE`
- `STAGE1_CUTOFF_QUANTILE`
- `STAGE2_START_DATE`
- `STAGE2_END_DATE`
- `STAGE2_CUTOFF_QUANTILE`

The stage-specific structural estimation remains intentionally different:

- stage 1 estimates in raw `spi` space
- stage 2 estimates in `strength` space

For each run, the active stage universe is used to re-estimate:

- `adjustment factor`
- `dynamism variable`
- `cutoff`

## Offensive And Defensive Metrics

The project uses the labels `xG` and `xGA` to describe adjusted offensive and defensive team metrics derived from historical goals and opponent strength. These are not shot-based expected goals models in the conventional event-data sense.

Instead, the metrics are built from:

- goals scored
- goals conceded
- opponent quality
- prior strength information
- correction logic for schedule imbalance

## Stage 1 Logic

Stage 1 uses the 2021 prior as a starting point and by default updates it over the 2021-05-26 to 2025-05-26 window.

At a high level, it:

1. loads the stage prior from `data/intermediate/spi_final.csv`
2. canonicalizes team names using `data/config/dictionary.csv`
3. filters the historical results to teams present in the prior universe
4. re-estimates `adjustment factor`, `dynamism variable`, and `cutoff` in raw `spi` space
5. applies a low-team adjustment regime below the configured cutoff
6. computes per-team xG and xGA
7. corrects those values for opponent strength exposure
8. rescales the outputs into goal-like units using the empirical median goals in the stage window
9. writes:
   - `data/intermediate/aggregated_xg_data.csv`
   - `data/intermediate/opponent_spi_data.csv`
   - `data/intermediate/confed/*.csv`

The stage 1 simulation then uses those confederation files to simulate all matchups and generate the next prior snapshot.

## Stage 2 Logic

Stage 2 is the currently active production method used for the latest rankings.

Its code implements a corrected, strength-balanced low-team approach:

1. The prior is converted into an internal strength scale.
2. `adjustment factor`, `dynamism variable`, and `cutoff` are re-estimated on that internal strength scale.
3. A low-team cutoff is derived on that internal strength scale.
4. High-strength teams use one reward regime.
5. Lower-strength teams use a corrected regime where:
   - offensive reward depends on actual opponent strength
   - own dampening is anchored at the cutoff
   - defensive penalties increase when conceding to weaker low-strength teams
6. Team metrics are corrected for opponent-strength exposure.
7. Outputs are rescaled using the empirical median goals in the relevant match window.
8. Confederation-level files are written and used for all-versus-all simulation.

This stage writes:

- `data/intermediate/aggregated_xg_data.csv`
- `data/intermediate/opponent_strength_data.csv`
- `data/intermediate/confed/*.csv`
- `data/output/ranking_final.csv`
- `ranking_final.csv`

## Simulation Method

The simulation step in both stages uses:

- offensive metric of team A
- defensive metric of team B
- offensive metric of team B
- defensive metric of team A

Expected goals are derived as simple averages:

- team A expected goals = `(team_a_xG + team_b_xGA) / 2`
- team B expected goals = `(team_b_xG + team_a_xGA) / 2`

Each matchup is then simulated repeatedly using Poisson-distributed goal counts. The pipeline currently uses a large all-versus-all Monte Carlo approach and converts simulated points into an SPI-like percentage scale.
The active simulation uses NumPy Poisson sampling, which keeps the same Monte Carlo structure while making reruns much faster than the earlier manual inverse-Poisson implementation.

## Outputs

### Intermediate Outputs

The active pipeline writes working files under:

- `data/intermediate/`

including:

- `spi_final.csv`
- `aggregated_xg_data.csv`
- `opponent_strength_data.csv`
- `opponent_spi_data.csv` when stage 1 is run
- `confed/AFC.csv`
- `confed/CAF.csv`
- `confed/CONCACAF.csv`
- `confed/CONMEBOL.csv`
- `confed/OFC.csv`
- `confed/UEFA.csv`

### Final Ranking Output

The final ranking output lives at:

- `data/output/ranking_final.csv`

and is also copied to:

- `ranking_final.csv`

The root copy exists so the Streamlit app and any external consumer that expects the old root file contract continue to work unchanged.

## Streamlit App Contract

The active app implementation lives in:

- `app/football_predictor.py`

The compatibility entrypoint lives at:

- `football_predictor.py`

That root file is intentionally a wrapper which runs the app implementation under `app/`. The app itself reads the local root `ranking_final.csv`, not archived legacy outputs.

## Operational Commands

Run from `/home/albertovth/football_predictor`.

Activate the intended environment first:

```bash
source ~/.bashrc >/dev/null 2>&1 || true
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate spyder607
```

### Stage 1

```bash
bash scripts/run_stage1.sh
```

### Stage 2

```bash
bash scripts/run_stage2.sh
```

### Full Ranking Update

```bash
bash scripts/update_rankings.sh
```

### Streamlit App

```bash
streamlit run football_predictor.py
```

## Limitations

- The model is driven primarily by scorelines and prior strength, not event-level shot data.
- It does not explicitly model home advantage, injuries, squad selection, travel, or tactical context.
- Match coverage and match frequency are uneven across teams.
- The rating world is intentionally counterfactual: team metrics are built in an adjusted all-versus-all-style framework rather than directly on the raw realized schedule.
- The current documentation reflects the repository structure and code as migrated; it does not claim that every archived historical experiment in `/home/albertovth/SPI` has been retained as active logic.
