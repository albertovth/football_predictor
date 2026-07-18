# Stage 4 national-team ranking update guide

This guide repeats the method that produced the validated Stage 3 ranking on
2026-07-18. Do not use archive, post_world_cup_update.py, or wrong_output.

Stage 4 has five parts:

1. Run unchanged Stage 2 calibration and raw xG/xGA using the published Stage 3
   ranking as the prior.
2. Combine raw metrics with the published cumulative evidence.
3. Run unchanged Stage 2 all-versus-all simulation.
4. Validate everything in isolation.
5. Publish only after every gate passes.

## Incoming Stage 4 prior

Use these files together:

- Ranking: data/config/priors/spi_global_rankings_intl_18_7_2026.csv
- Evidence: data/config/priors/ranking_evidence_18_7_2026.csv

Ranking SHA-256:

    ffd346a5d512d6754885f35207ebc17ff9155363f7ec199e5ec548371dccebb1

The evidence file contains each team's total through Stage 3. Do not run
build_prior_evidence.py again. That one-time script reconstructed the first
cumulative prior from Stage 1 plus Stage 2.

## Exact Stage 4 start

The Stage 3 source cutoff was July 18, but its last completed eligible match was
July 15. France-England on July 18 and Spain-Argentina on July 19 were not
included.

- Incoming prior last included match: 2026-07-15
- Stage 4 start: 2026-07-16
- Stage 4 end: the new frozen-source cutoff

Always derive the start from the last completed eligible match actually
included. Do not infer it from a filename or publication date.

## Local Python environment

Validated interpreter:

    /home/albertovth/anaconda3/envs/spyder607/bin/python

The all-versus-all calculation runs locally and retains 10,000 simulations for
every ordered matchup.

Suggested variables:

    STAGE4_RUN=data/output/stage4_YYYY_MM_DD
    STAGE4_INPUT=data/input/stage4_YYYY_MM_DD/results.csv
    STAGE4_PRIOR=data/config/priors/spi_global_rankings_intl_18_7_2026.csv
    STAGE4_EVIDENCE=data/config/priors/ranking_evidence_18_7_2026.csv
    STAGE4_START=2026-07-16
    STAGE4_END=YYYY-MM-DD
    SPYDER_PYTHON=/home/albertovth/anaconda3/envs/spyder607/bin/python

Create isolated output directories:

    mkdir -p "$STAGE4_RUN/raw/intermediate/confed"
    mkdir -p "$STAGE4_RUN/intermediate/confed"
    mkdir -p "$STAGE4_RUN/output"
    mkdir -p "$STAGE4_RUN/logs"
    mkdir -p "$STAGE4_RUN/reproducibility"

Never point a pre-validation command at live ranking_final.csv.

## 1. Freeze and audit results

Save the exact results snapshot to STAGE4_INPUT and record:

- source URL and upstream commit;
- retrieval time;
- SHA-256;
- configured start and end dates;
- completed and unfinished rows.

Use data/config/dictionary.csv for backend mapping while preserving UI names.
Add a mapping only for a genuine alias of an existing country.

Create audit files for:

- all completed rows;
- eligible rows;
- excluded rows with reasons;
- unfinished rows;
- team source/backend/UI mappings.

Count friendlies, World Cup matches, and other competitive matches separately.
Check duplicate keys using:

    date, home_team, away_team, home_score, away_score, tournament

Reject malformed, negative, or fractional completed scores. No match dated
before STAGE4_START may enter the new sample.

## 2. Initialize the published prior

Run:

    FOOTBALL_DATA_DIR="$PWD/data" \
    FOOTBALL_INTERMEDIATE_DIR="$PWD/$STAGE4_RUN/raw/intermediate" \
    FOOTBALL_STAGE2_PRIOR_FILE="$PWD/$STAGE4_PRIOR" \
    FOOTBALL_RESULTS_SOURCE="$PWD/$STAGE4_INPUT" \
    STAGE2_START_DATE="$STAGE4_START" \
    STAGE2_END_DATE="$STAGE4_END" \
    "$SPYDER_PYTHON" pipeline/spi_stage2/init_from_spi_538.py \
      > "$STAGE4_RUN/logs/01_init_prior.log"

Confirm 206 rows, exact UI names, prior top rows, and prior SHA. Do not use
spi_global_rankings_intl_26_5_2025.csv.

## 3. Run calibration helpers

Adjustment factor and dynamism:

    FOOTBALL_DATA_DIR="$PWD/data" \
    FOOTBALL_INTERMEDIATE_DIR="$PWD/$STAGE4_RUN/raw/intermediate" \
    FOOTBALL_STAGE2_PRIOR_FILE="$PWD/$STAGE4_PRIOR" \
    FOOTBALL_RESULTS_SOURCE="$PWD/$STAGE4_INPUT" \
    STAGE2_START_DATE="$STAGE4_START" \
    STAGE2_END_DATE="$STAGE4_END" \
    STAGE2_CUTOFF_QUANTILE=0.07 \
    "$SPYDER_PYTHON" pipeline/spi_stage2/calculate_adjustment_factor.py \
      > "$STAGE4_RUN/logs/02_adjustment_factor.log"

Diagnostic cap calculation:

    FOOTBALL_DATA_DIR="$PWD/data" \
    FOOTBALL_INTERMEDIATE_DIR="$PWD/$STAGE4_RUN/raw/intermediate" \
    FOOTBALL_STAGE2_PRIOR_FILE="$PWD/$STAGE4_PRIOR" \
    FOOTBALL_RESULTS_SOURCE="$PWD/$STAGE4_INPUT" \
    STAGE2_START_DATE="$STAGE4_START" \
    STAGE2_END_DATE="$STAGE4_END" \
    "$SPYDER_PYTHON" pipeline/spi_stage2/calculate_caps_off_def.py \
      > "$STAGE4_RUN/logs/03_caps_off_def.log"

Cutoff search:

    FOOTBALL_DATA_DIR="$PWD/data" \
    FOOTBALL_INTERMEDIATE_DIR="$PWD/$STAGE4_RUN/raw/intermediate" \
    FOOTBALL_STAGE2_PRIOR_FILE="$PWD/$STAGE4_PRIOR" \
    FOOTBALL_RESULTS_SOURCE="$PWD/$STAGE4_INPUT" \
    STAGE2_START_DATE="$STAGE4_START" \
    STAGE2_END_DATE="$STAGE4_END" \
    "$SPYDER_PYTHON" pipeline/spi_stage2/calculate_low_team_cutoff.py \
      > "$STAGE4_RUN/logs/04_low_team_cutoff.log"

Use the unchanged search's selected quantile. If none of 1 percent through 25
percent qualifies, retain the documented 7 percent fallback. Never silently
assume 7 percent.

The cap helper is a recorded diagnostic. Unchanged calculate_xg_xga.py does not
consume its printed values and retains the established hard cap of 6.

## 4. Exact calibration order

Do not reorder these operations:

1. Rank-normalize incoming prior SPI to 0.05 through 0.95.
2. Compute minimum, median, maximum, and cutoff strength.
3. Derive adjustment factor.
4. Search dynamism.
5. Derive low-team defensive P_c.
6. Filter the inclusive update window and remove unfinished rows.
7. Map aliases to backend names.
8. Restrict to the prior universe.
9. Multiply friendly goals by 0.5 before metric calculation.
10. Apply the existing high/high or low-team branch.
11. Apply existing floors and hard caps.
12. Average adjusted xG and xGA by matches.
13. Calculate average and median opponent strengths.
14. Apply offense and defense opponent corrections.
15. Calculate and apply corrected-xGA 95th-percentile cap.
16. Calculate corrected xG and clipped xGA medians.
17. Calculate the unweighted empirical goal median for the date window.
18. Scale raw xG and xGA to the empirical median.
19. Carry zero-match teams from the prior on the new scale.
20. Save raw metrics and opponent correction.

The formulas live only in pipeline/spi_stage2/calculate_xg_xga.py. Do not
reimplement them.

## 5. Calculate raw Stage 4 metrics

Replace 0.07 below only if the unchanged cutoff search selected another value:

    FOOTBALL_DATA_DIR="$PWD/data" \
    FOOTBALL_INTERMEDIATE_DIR="$PWD/$STAGE4_RUN/raw/intermediate" \
    FOOTBALL_STAGE2_PRIOR_FILE="$PWD/$STAGE4_PRIOR" \
    FOOTBALL_RESULTS_SOURCE="$PWD/$STAGE4_INPUT" \
    STAGE2_START_DATE="$STAGE4_START" \
    STAGE2_END_DATE="$STAGE4_END" \
    STAGE2_CUTOFF_QUANTILE=0.07 \
    "$SPYDER_PYTHON" pipeline/spi_stage2/calculate_xg_xga.py \
      > "$STAGE4_RUN/logs/05_calculate_raw_xg_xga.log"

Preserve raw/intermediate/aggregated_xg_data.csv,
raw/intermediate/opponent_strength_data.csv, confederation files, and the log.

## 6. Combine cumulative evidence

Run:

    "$SPYDER_PYTHON" pipeline/spi_stage3/combine_prior_evidence.py \
      --prior-ranking "$STAGE4_PRIOR" \
      --prior-evidence "$STAGE4_EVIDENCE" \
      --new-metrics "$STAGE4_RUN/raw/intermediate/aggregated_xg_data.csv" \
      --dictionary data/config/dictionary.csv \
      --results "$STAGE4_INPUT" \
      --start-date "$STAGE4_START" \
      --end-date "$STAGE4_END" \
      --aggregated-output "$STAGE4_RUN/intermediate/aggregated_xg_data.csv" \
      --confed-output-dir "$STAGE4_RUN/intermediate/confed" \
      --calibration-output "$STAGE4_RUN/evidence_calibration.csv" \
      --evidence-output "$STAGE4_RUN/evidence_final.csv" \
      --audit-output "$STAGE4_RUN/evidence_normalization.csv" \
      > "$STAGE4_RUN/logs/06_combine_prior_evidence.log"

For xG and xGA separately:

    scaled prior xG =
        (team prior xG / median prior xG) * empirical median goals

    scaled prior xGA =
        (team prior xGA / median prior xGA) * empirical median goals

    pooled metric =
        (scaled prior metric * prior matches + new metric * new matches)
        / (prior matches + new matches)

The prior's exact xG/xGA numbers are therefore not carried as absolute values.
Its relative offensive and defensive positions are transferred independently
to the new period's median-goal scale. The `new metric` in the pooling formula
is calculated only from matches in the new date window.

The script then normalizes both pooled 206-team distributions to empirical
median goals. A zero-match team has new matches equal to zero and therefore
preserves its prior relative xG and xGA placements. A team with only a few new
matches receives the same arithmetic weighting rule as every other team.

The resulting evidence_final.csv becomes the next update's evidence prior.

## 7. Run unchanged simulation

Normal production behavior is unseeded:

    FOOTBALL_DATA_DIR="$PWD/data" \
    FOOTBALL_INTERMEDIATE_DIR="$PWD/$STAGE4_RUN/intermediate" \
    FOOTBALL_OUTPUT_DIR="$PWD/$STAGE4_RUN/output" \
    FOOTBALL_RANKING_OUTPUT_FILE="$PWD/$STAGE4_RUN/output/ranking_final.csv" \
    FOOTBALL_ROOT_RANKING_FILE="$PWD/$STAGE4_RUN/output/root_ranking_final.csv" \
    FOOTBALL_RESULTS_SOURCE="$PWD/$STAGE4_INPUT" \
    STAGE2_START_DATE="$STAGE4_START" \
    STAGE2_END_DATE="$STAGE4_END" \
    "$SPYDER_PYTHON" pipeline/spi_stage2/simulate_spi.py \
      > "$STAGE4_RUN/logs/07_production_simulation.log"

For reproducibility, run the same script twice into separate audit directories
using:

    "$SPYDER_PYTHON" -c "import numpy as np, runpy; np.random.seed(YYYYMMDD); runpy.run_path('pipeline/spi_stage2/simulate_spi.py', run_name='__main__')"

Supply the same path and date environment variables as the production command,
but separate output files. The two ranking SHA-256 hashes must match.

## 8. Mandatory validation gates

Do not publish unless all pass:

- exact incoming ranking and evidence SHAs recorded;
- exact prior last-included, new-start, and source-cutoff dates;
- completed, unfinished, eligible, and excluded counts reconcile;
- category counts reconcile;
- no duplicate matches;
- no prior overlap;
- no malformed or fabricated scores;
- unfinished matches excluded;
- every excluded row has a reason;
- every eligible backend team exists in the prior;
- final UI-name set exactly equals the prior UI-name set;
- aliases round-trip correctly;
- friendly goals are multiplied exactly by 0.5;
- raw and pooled metrics are finite and nonnegative;
- pooled medians equal empirical median goals;
- evidence arithmetic is exact;
- zero-match teams preserve relative xG and xGA order;
- ranks are exactly 1 through 206;
- prior regression metrics reproduce;
- empty-new-window combination returns prior metrics;
- two seeded simulations are byte-identical;
- formulas and order have no unintended diff;
- repository tests pass.

Inspect rank movements and football plausibility as rejection gates. Never tune
parameters to force a named country to a desired rank.

## 9. Required output package

Keep:

- frozen results and SHA;
- prior ranking and evidence copies;
- all calibration logs;
- cutoff output;
- raw adjusted xG/xGA;
- opponent corrections;
- evidence calibration;
- pooled xG/xGA;
- next-stage evidence;
- seeded audit outputs;
- unseeded production ranking;
- ranking comparison;
- excluded, unfinished, mapping, and warnings reports;
- machine-readable validation report;
- parameter JSON and previous/new parameter table.

## 10. Publication

Only after validation:

    cp "$STAGE4_RUN/output/ranking_final.csv" ranking_final.csv
    cp "$STAGE4_RUN/output/ranking_final.csv" data/output/ranking_final.csv
    cp "$STAGE4_RUN/output/ranking_final.csv" \
      data/config/priors/spi_global_rankings_intl_D_M_YYYY.csv
    cp "$STAGE4_RUN/evidence_final.csv" data/output/ranking_evidence.csv
    cp "$STAGE4_RUN/evidence_final.csv" \
      data/config/priors/ranking_evidence_D_M_YYYY.csv

Verify identical ranking SHAs, then run:

    "$SPYDER_PYTHON" -m pytest -q

Open the app locally and verify all 206 teams and UI aliases such as China PR,
Congo DR, and USA.

## Stage 3 regression reference

These values regression-test the workflow. Stage 4 must derive its own values:

- strength interval: 0.05 through 0.95;
- strength median: 0.5;
- cutoff quantile: 0.07;
- cutoff strength: 0.113;
- adjustment factor: 0.33277777777777784;
- dynamism: 0.025;
- low-team defensive P_c: 3.784242871189775;
- corrected xGA cap: 8.396484358315535;
- corrected xG median: 3.7030226644707422;
- clipped xGA median: 2.9596064068731396;
- empirical median goals: 1.0;
- offensive scale: 0.27004965689102145;
- defensive scale: 0.3378827663292269;
- simulations per ordered matchup: 10,000.
