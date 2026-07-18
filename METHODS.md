# Methods

This document describes the active methodology implemented in the reorganized repository at `/home/albertovth/football_predictor`.

It is aligned with the current code under:

- `app/`
- `src/football_predictor/`
- `pipeline/spi_stage1/`
- `pipeline/spi_stage2/`
- `pipeline/spi_stage3/`
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

The repository currently keeps two historical calculation stages and one
evidence-update layer:

- `pipeline/spi_stage1/`
- `pipeline/spi_stage2/`
- `pipeline/spi_stage3/`

Stage 1 produces the May 2025 prior. Stage 2 contains the current corrected and
balanced calculation and simulation engine. Stage 3 reuses that engine with a
new prior and new date window, then stabilizes sparse samples by transferring
the prior's relative xG/xGA positions to the new median scale and weighting
them against new match appearances.

## Repository Roles In The Method

### `pipeline/spi_stage1/`

Stage 1 contains:

- `init_from_spi_538.py`
- `calculate_xg_xga.py`
- `simulate_spi.py`

This historical stage:

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

As the reusable production engine, this stage:

- accepts the stage-specific prior through configuration (the dated May 2025
  file is only the original Stage 2 default)
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

The historical pipeline and next-update workflow use these prior files:

- `data/config/priors/spi_global_rankings_intl_25_5_2021.csv`
- `data/config/priors/spi_global_rankings_intl_26_5_2025.csv`
- `data/config/priors/spi_global_rankings_intl_18_7_2026.csv`
- `data/config/priors/ranking_evidence_18_7_2026.csv`

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

Stage 2 is the active formula and simulation engine. Later numbered updates
reconfigure this engine with their own prior, dates, and recalibrated values.

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

## Stage 3 Evidence Logic

Stage 3 calculates raw xG/xGA only from the new match window using the Stage 2
engine. It then transfers each prior metric by relative median position:

- scaled prior xG = `(team prior xG / median prior xG) * new goal median`
- scaled prior xGA = `(team prior xGA / median prior xGA) * new goal median`

Each transferred metric is weighted against the raw new-period metric using
prior and new team appearances. The pooled 206-team xG and xGA distributions
are normalized independently to the new empirical goal median before the
unchanged simulation runs. Teams without a new match therefore preserve their
relative prior positions; teams with few matches move in proportion to their
new evidence.

In the full replay, prior appearances are read from a dated four-year rolling
ledger at the Stage 2 and Stage 3 handoffs. Every appearance inside the window
has weight one; older appearances have weight zero. There is no additional
decay curve or fitted coefficient. Four-year and cumulative pooling were
effectively tied over 240
chronologically held-out matches, while direct replacement was materially
worse. The four-year boundary is therefore a transparent one-World-Cup-cycle
policy rather than a claimed optimized duration.

This bounds evidence confidence rather than erasing all inherited memory.
Persistent institutions and competence can remain represented in a carried
prior and are progressively diluted by new appearances.

The exact next-update procedure is in `docs/STAGE4_UPDATE_GUIDE.md`.

## Simulation Method

The simulation step used by the calculation stages and later updates uses:

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

### Streamlit App Score Suggestion

The Streamlit app first keeps its existing winner/draw forecast logic based on the 10,000 simulated outcomes. After that outcome is selected, candidate scorelines are constrained to that forecasted outcome.

Within that set, the displayed scoreline is chosen by a 5/3/1 criteria point system that prioritizes exact result, goal difference and winner: 5 points for exact score, 3 for correct goal difference, and 1 for correct winner or draw. The app evaluates each candidate scoreline against all simulated match results and selects the scoreline with the highest average points.

Because the candidate scores already share the selected outcome, the winner criterion is included for consistency with the point system, while exact score and goal difference do most of the work when choosing between scores for the same forecasted winner or draw.

This is more complete than simply picking the modal score. The most frequent simulated score is often only slightly more common than several nearby scores. The point-maximizing approach evaluates a wider range of outcomes and selects the score that gives the best average return when exact score, goal difference and correct winner are all considered, with exact score weighted highest and goal difference weighted next.

This means the suggested scoreline is not necessarily the single most frequent simulated score.

## Limitations

- The model is driven primarily by scorelines and prior strength, not event-level shot data.
- It does not explicitly model home advantage, injuries, squad selection, travel, or tactical context.
- Match coverage and match frequency are uneven across teams.
- The rating world is intentionally counterfactual: team metrics are built in an adjusted all-versus-all-style framework rather than directly on the raw realized schedule.
- The current documentation reflects the repository structure and code as migrated; it does not claim that every archived historical experiment in `/home/albertovth/SPI` has been retained as active logic.
