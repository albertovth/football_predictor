# Stage 4 national-team ranking update guide

This guide records the validated Stage 4 update published on 2026-07-20 and is
the repeatable template for later rolling updates. Do not use archive,
post_world_cup_update.py, or wrong_output.

Stage 4 has five parts:

1. Run the production Stage 2 calibration and raw xG/xGA using the published
   ranking as the prior.
2. Combine raw metrics with the published four-year evidence window.
3. Run unchanged Stage 2 all-versus-all simulation.
4. Validate everything in isolation.
5. Publish only after every gate passes.

## Incoming Stage 4 prior

Use these files together:

- Ranking: data/config/priors/spi_global_rankings_intl_18_7_2026.csv
- Evidence: data/config/priors/ranking_evidence_18_7_2026.csv
- Dated evidence ledger:
  data/config/priors/ranking_evidence_ledger_18_7_2026.csv

Ranking SHA-256:

    88aff21cee6585e14b8ce313489b48ac05342b3cdc8bfe669d859fd47e3918e3

Evidence SHA-256:

    2af8f7a13647547eb9ce14e0ab50c11477bf1b88e703d04700abdcf062459cfb

Ledger SHA-256:

    44f84f23f8d96f3a120fbc11f9554abcbb380a02df62dd59a9a3b7463433278a

The evidence file is the 206-team aggregate of the ledger. The ledger contains
one row per eligible team appearance and is what allows old appearances to
expire. Do not substitute the earlier cumulative evidence_final.csv.

The incoming ranking was rebuilt sequentially from the May 2021 FiveThirtyEight
prior, with four-year evidence pooling at both later handoffs. Stage 4
transfers that published Stage 3 xG/xGA by relative position, calculates raw
metrics only from the new window, and combines the two sources using the
evidence counts below. The replay audit is under
`data/output/stage3_replay_from_2021_2026_07_18/`.

The completed Stage 4 publication uses:

- ranking: `data/config/priors/spi_global_rankings_intl_20_7_2026.csv`;
- evidence: `data/config/priors/ranking_evidence_20_7_2026.csv`;
- ledger: `data/config/priors/ranking_evidence_ledger_20_7_2026.csv`;
- full audit: `data/output/stage4_2026_07_20/`.

## Exact Stage 4 start

The Stage 3 source cutoff was July 18, but its last completed eligible match was
July 15. France-England on July 18 and Spain-Argentina on July 19 were not
included.

- Incoming prior last included match: 2026-07-15
- Stage 4 start: 2026-07-16
- Stage 4 end: 2026-07-19
- Incoming four-year evidence window: 2022-07-16 through 2026-07-15
- Updated evidence and goal-median window: 2022-07-20 through 2026-07-19

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
    STAGE4_GOAL_MEDIAN=data/input/stage4_YYYY_MM_DD/goal_median_results.csv
    STAGE4_PRIOR=data/config/priors/spi_global_rankings_intl_18_7_2026.csv
    STAGE4_EVIDENCE=data/config/priors/ranking_evidence_18_7_2026.csv
    STAGE4_LEDGER=data/config/priors/ranking_evidence_ledger_18_7_2026.csv
    STAGE4_START=2026-07-16
    STAGE4_END=YYYY-MM-DD
    STAGE4_LAST_INCLUDED=YYYY-MM-DD
    GOAL_MEDIAN_START=YYYY-MM-DD
    GOAL_MEDIAN_END=YYYY-MM-DD
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

Also freeze `STAGE4_GOAL_MEDIAN`: every completed source result in the
inclusive rolling four-year window ending at the update cutoff. This file is
used only for the common empirical raw-goal scale. It does not add old matches
to the new-period xG/xGA calculation.

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
    FOOTBALL_GOAL_MEDIAN_RESULTS_SOURCE="$PWD/$STAGE4_GOAL_MEDIAN" \
    GOAL_MEDIAN_START_DATE="$GOAL_MEDIAN_START" \
    GOAL_MEDIAN_END_DATE="$GOAL_MEDIAN_END" \
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
    FOOTBALL_GOAL_MEDIAN_RESULTS_SOURCE="$PWD/$STAGE4_GOAL_MEDIAN" \
    GOAL_MEDIAN_START_DATE="$GOAL_MEDIAN_START" \
    GOAL_MEDIAN_END_DATE="$GOAL_MEDIAN_END" \
    STAGE2_START_DATE="$STAGE4_START" \
    STAGE2_END_DATE="$STAGE4_END" \
    "$SPYDER_PYTHON" pipeline/spi_stage2/calculate_low_team_cutoff.py \
      > "$STAGE4_RUN/logs/04_low_team_cutoff.log"

Use the production search's selected quantile. Teams without a new match are
not synthetic zero-metric observations in this diagnostic. If none of 1
percent through 25 percent qualifies, retain the documented 7 percent fallback.
Never silently assume 7 percent.

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
17. Calculate the unweighted empirical raw-goal median from the same rolling
    four-year window used for evidence confidence.
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
    FOOTBALL_GOAL_MEDIAN_RESULTS_SOURCE="$PWD/$STAGE4_GOAL_MEDIAN" \
    GOAL_MEDIAN_START_DATE="$GOAL_MEDIAN_START" \
    GOAL_MEDIAN_END_DATE="$GOAL_MEDIAN_END" \
    STAGE2_START_DATE="$STAGE4_START" \
    STAGE2_END_DATE="$STAGE4_END" \
    STAGE2_CUTOFF_QUANTILE=0.07 \
    "$SPYDER_PYTHON" pipeline/spi_stage2/calculate_xg_xga.py \
      > "$STAGE4_RUN/logs/05_calculate_raw_xg_xga.log"

Preserve raw/intermediate/aggregated_xg_data.csv,
raw/intermediate/opponent_strength_data.csv, confederation files, and the log.

## 6. Combine the four-year evidence window

Run:

    "$SPYDER_PYTHON" pipeline/spi_stage3/combine_prior_evidence.py \
      --prior-ranking "$STAGE4_PRIOR" \
      --prior-evidence "$STAGE4_EVIDENCE" \
      --prior-evidence-ledger "$STAGE4_LEDGER" \
      --new-metrics "$STAGE4_RUN/raw/intermediate/aggregated_xg_data.csv" \
      --dictionary data/config/dictionary.csv \
      --results "$STAGE4_INPUT" \
      --start-date "$STAGE4_START" \
      --end-date "$STAGE4_END" \
      --goal-median-results "$STAGE4_GOAL_MEDIAN" \
      --goal-median-start-date "$GOAL_MEDIAN_START" \
      --goal-median-end-date "$GOAL_MEDIAN_END" \
      --aggregated-output "$STAGE4_RUN/intermediate/aggregated_xg_data.csv" \
      --confed-output-dir "$STAGE4_RUN/intermediate/confed" \
      --calibration-output "$STAGE4_RUN/evidence_calibration.csv" \
      --evidence-output "$STAGE4_RUN/evidence_final.csv" \
      --evidence-ledger-output "$STAGE4_RUN/evidence_ledger_final.csv" \
      --windowed-prior-output "$STAGE4_RUN/windowed_prior_evidence.csv" \
      --evidence-cutoff-date "$STAGE4_LAST_INCLUDED" \
      --evidence-window-years 4 \
      --stage-label stage4 \
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

There is no fitted decay, multiplier, or pseudo-count. Every retained eligible
appearance has weight one; every appearance older than four years has weight
zero. Therefore a team with 36 retained prior appearances and four new matches
gets prior weight 36/40 and new weight 4/40. Those shares come from observed
match counts, not a selected coefficient.

For an automated update, the rolling start is always:

    cron run/update cutoff date - 4 calendar years + 1 day

The evidence ledger and empirical goal-median source must use that same start
and cutoff. For example, a cron run on 2026-08-20 uses 2022-08-21 through
2026-08-20, regardless of the exact day of the latest match inside that period.
The new-match start remains the day after the last match already in the prior.

The resulting evidence_final.csv and evidence_ledger_final.csv become the next
update's evidence prior pair.

### Empirical check and scope

The four-year rule was compared chronologically with cumulative pooling,
direct new-period replacement, and leaving the prior unchanged over 240 held-
out matches. Mean Poisson negative log likelihood per match was:

- cumulative pooling: 3.028577;
- four-year pooling: 3.028928;
- prior only: 3.032991;
- direct replacement: 3.172841.

Four-year and cumulative pooling each won two of four folds and were
effectively tied. This supports match-count pooling and rejects direct
replacement. It does not prove that four years is an optimized duration. Four
years is the bounded one-World-Cup-cycle policy, adopted without measurable
holdout degradation and without adding a fitted parameter. Exact fold scores
are in data/output/stage3_2026_07_18/evidence_window_holdout.csv.

This is a rolling evidence-confidence window. Expiring an appearance reduces
the incoming prior's confidence weight; it does not algebraically remove that
match from an already-published prior xG/xGA value.

## 7. Run unchanged simulation

Normal production behavior is unseeded:

    FOOTBALL_DATA_DIR="$PWD/data" \
    FOOTBALL_INTERMEDIATE_DIR="$PWD/$STAGE4_RUN/intermediate" \
    FOOTBALL_OUTPUT_DIR="$PWD/$STAGE4_RUN/output" \
    FOOTBALL_RANKING_OUTPUT_FILE="$PWD/$STAGE4_RUN/output/ranking_final.csv" \
    FOOTBALL_ROOT_RANKING_FILE="$PWD/$STAGE4_RUN/output/root_ranking_final.csv" \
    FOOTBALL_RESULTS_SOURCE="$PWD/$STAGE4_INPUT" \
    FOOTBALL_GOAL_MEDIAN_RESULTS_SOURCE="$PWD/$STAGE4_GOAL_MEDIAN" \
    GOAL_MEDIAN_START_DATE="$GOAL_MEDIAN_START" \
    GOAL_MEDIAN_END_DATE="$GOAL_MEDIAN_END" \
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
- exact incoming ledger SHA recorded;
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
- new metric match counts exactly equal new ledger appearance counts by team;
- every ledger date falls inside the four-year window;
- the window start equals the update cutoff date minus four years plus one day;
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
- next-stage dated evidence ledger;
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
    cp "$STAGE4_RUN/evidence_ledger_final.csv" data/output/ranking_evidence_ledger.csv
    cp "$STAGE4_RUN/evidence_ledger_final.csv" \
      data/config/priors/ranking_evidence_ledger_D_M_YYYY.csv

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
- corrected xGA cap: 10.165230613969603;
- empirical median goals: 1.0;
- retained prior appearances: 7,010;
- new appearances: 754;
- final rolling appearances: 7,764;
- simulations per ordered matchup: 10,000.

All exact replay values are in
`data/output/stage3_replay_from_2021_2026_07_18/parameter_comparison.csv`.

## Guarded monthly automation

`scripts/update_rankings.sh` now runs the fail-closed rolling workflow.
It checks monthly but only calculates and publishes when at least 100 completed,
eligible matches have accumulated after the published ledger cutoff:

    bash scripts/update_rankings.sh

The threshold is an evidence gate, not a weighting coefficient. If fewer than
100 matches exist, the command records the source audit and exits without
touching the app ranking. When the gate passes it freezes and maps the source,
derives the four-year dates from that run date, runs all calibration and
simulation steps in isolation, rejects non-finite diagnostics, runs two seeded
reproducibility checks and the test suite, and publishes atomically only after
every gate passes.

The automatic cutoff gate retains the unchanged 1%-25% search and the
documented 7% fallback. If the search selects any value other than 7%, the
wrapper repeats the raw metric calculation, evidence pooling, and all-versus-all
simulation at 7% with the same deterministic seed. The selected and 7% pooled
xG/xGA files and seeded rankings must be byte-identical. Otherwise publication
stops, the current ranking remains untouched, and ntfy reports that manual
review is required. A selected 7%, or a harmless non-7% result that is exactly
identical to 7%, continues automatically.

The installed cron runs at 04:15 Europe/Oslo on the 20th of every month.
`flock` prevents overlapping runs. Logs and frozen inputs are under
`data/output/automatic_YYYYMMDD/` and
`data/input/automatic_YYYYMMDD/`. Setting
`FOOTBALL_AUTO_GIT_PUSH=1` also commits and pushes only the published
ranking/evidence files after validation.

The cron reuses the existing private `NTFY_TOPIC` from
environment/secrets. It sends a normal-priority success message after
publication, a low-priority good-to-know message when the 100-match gate is not
yet met, and an urgent message for actionable failures. Notification delivery
errors are written to the run's `ntfy.log` and cannot recursively
trigger more notifications. The old World Cup result/fixture cron is commented
out and no related systemd timer is active, so its old failure notifier cannot
currently send messages.
