# Stage 4 validation report (20 July 2026)

Publication ready: **TRUE**

- Exact prior: `data/config/priors/spi_global_rankings_intl_18_7_2026.csv`
- Prior SHA-256: `88aff21cee6585e14b8ce313489b48ac05342b3cdc8bfe669d859fd47e3918e3`
- Prior last included match: 2026-07-15
- New match window: 2026-07-16 through 2026-07-19
- Completed/eligible new matches: 2/2 (2 World Cup, 0 friendly, 0 other)
- Excluded, unfinished, malformed, unmatched, duplicate: 0 each
- Rolling evidence window: 2022-07-20 through 2026-07-19
- Retained prior appearances: 7,756; added: 4; expired: 8; final: 7,760
- Goal-median source: 4,048 completed matches / 8,096 team scores
- Empirical goal median: 1.0 (rejected two-match baseline: 2.5)
- Candidate teams: 206; seeded runs: byte-identical
- Tests: 23 passed

## Ranking outcome

Top six: Argentina, Spain, Brazil, France, Netherlands, England. All rank changes are at most one place. Two new matches affect evidence-weighted xG/xGA without overwhelming the retained window.

## Median correction

Every normalization point uses the frozen four-year rolling results window. The rejected two-match-scale candidate is preserved under `audit/rejected_incremental_median/` and was never published.

## Diagnostics

The production cutoff helper selected 1%; the 7% sensitivity output is byte-identical. No-match teams are excluded from the cutoff diagnostic and carried from the prior in production. The two-match cap diagnostic returned NaN, but is not consumed; established hard caps remain 6. The automated workflow requires 100 matches and fails closed on any non-finite calibration log.

## Checks

- PASS — exact_prior_sha
- PASS — prior_206_teams
- PASS — candidate_206_teams
- PASS — ui_names_preserved
- PASS — new_window_exact
- PASS — category_counts
- PASS — no_new_duplicates
- PASS — completed_integer_scores
- PASS — no_prior_overlap
- PASS — normalization_window_exact
- PASS — normalization_4048_completed_matches
- PASS — normalization_no_duplicates
- PASS — normalization_median_one
- PASS — finite_raw_metrics
- PASS — finite_pooled_metrics
- PASS — pooled_metric_medians_one
- PASS — raw_match_appearances_four
- PASS — exact_played_teams
- PASS — evidence_counts_match_ledger
- PASS — stage4_ledger_four_appearances
- PASS — no_ledger_duplicates
- PASS — seeded_reproducibility
- PASS — cutoff_sensitivity_identical
- PASS — friendly_half_weighting_present
- PASS — zero_match_relative_xg_preserved
- PASS — zero_match_relative_xga_preserved
- PASS — empty_update_preserves_relative_xg
- PASS — empty_update_preserves_relative_xga
