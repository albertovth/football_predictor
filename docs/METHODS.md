# Current national-team ranking method

Status: authoritative for the validated Stage 3 ranking published on
2026-07-18. For operational commands for the next update, use
`docs/STAGE4_UPDATE_GUIDE.md`.

## Pipeline history

- Stage 1 started from the May 2021 FiveThirtyEight international SPI prior and
  processed matches from 2021-05-26 through 2025-05-26.
- Stage 2 used the Stage 1 result as its prior and processed matches from
  2025-05-27 through 2026-01-26.
- Stage 3 used the then-current 206-team application `ranking_final.csv` as its
  prior and processed new matches from 2026-01-27. The last eligible completed
  match in the frozen source was 2026-07-15.

The Stage 3 prior was the ranking beginning Spain, England, and France. It was
not the older file named `spi_global_rankings_intl_26_5_2025.csv`.

## Authoritative code

The active production calculation remains in:

- `pipeline/spi_stage1/`
- `pipeline/spi_stage2/`
- `src/football_predictor/stage_config.py`

Stage 3 deliberately calls `pipeline/spi_stage2/calculate_xg_xga.py` and
`pipeline/spi_stage2/simulate_spi.py`. Reusing those scripts means reusing the
established formulas and calculation order; it does not mean reusing the Stage
2 prior, dates, match sample, or derived parameters.

The Stage 3-specific evidence layer is implemented in:

- `pipeline/spi_stage3/build_prior_evidence.py`
- `pipeline/spi_stage3/combine_prior_evidence.py`

Do not use `archive/`, `src/football_predictor/post_world_cup_update.py`,
`wrong_output`, or custom post-World-Cup scripts for a production ranking.

## Raw new-period xG and xGA

Raw Stage 3 xG and xGA are calculated only from eligible matches in the new
Stage 3 window. Old matches are not reprocessed to create the new-period
metrics.

The production order is:

1. Load the exact incoming ranking and rank-normalize its SPI distribution to
   0.05 through 0.95.
2. Derive the adjustment factor, dynamism, cutoff search, cutoff strength, and
   low-team defensive anchor from the configured prior and calibration sample.
3. Filter the inclusive date window and exclude unfinished or ineligible rows.
4. Map source aliases to backend teams while retaining the prior's UI names.
5. Multiply friendly goals by exactly 0.5 before metric calculation.
6. Apply the established high-team/low-team adjusted-goal branches, rewards,
   penalties, floors, and caps.
7. Average adjusted xG and xGA by team appearances.
8. Calculate opponent mean and median strengths and apply the existing
   opponent corrections.
9. Calculate and apply the corrected-xGA percentile cap.
10. Derive corrected metric medians, the empirical median goals, and offensive
    and defensive scaling.
11. Write raw xG/xGA and confederation inputs.

The labels xG and xGA are goal- and opponent-adjusted team metrics; they are
not shot-event expected-goal models.

## Relative prior transfer and evidence weighting

An incoming prior's xG and xGA are not treated as permanent absolute goal
values. They are first expressed relative to their respective prior
distributions and transferred to the new period's empirical median-goal scale:

```text
scaled prior xG =
    (team prior xG / median prior xG) * new empirical median goals

scaled prior xGA =
    (team prior xGA / median prior xGA) * new empirical median goals
```

For a team with new matches, each metric is then combined independently:

```text
pooled metric =
    (scaled prior metric * prior evidence appearances
     + raw new-period metric * new-period appearances)
    / (prior evidence appearances + new-period appearances)
```

The complete 206-team pooled xG and xGA distributions are then independently
normalized to the new empirical median goals.

This distinction is important:

- A team's raw new-period metric is based only on its new matches.
- Prior evidence counts control confidence in its incoming relative position;
  they do not cause old goals to be recalculated.
- A team with few new matches moves modestly because both sources are weighted.
- A team with no new matches has new weight zero and therefore preserves its
  relative prior xG and xGA positions on the new scale.

The first Stage 3 update reconstructed prior evidence counts from the eligible
Stage 1 and Stage 2 team appearances. Later updates use the published
`ranking_evidence_*.csv` file and add only the new window's appearances. Do not
recount Stage 1 and Stage 2 for every future update.

## Simulation

The final pooled confederation files are consumed by the unchanged production
simulation. For teams A and B:

```text
A expected goals = (A xG + B xGA) / 2
B expected goals = (B xG + A xGA) / 2
```

Every ordered matchup uses 10,000 Poisson simulations. Points are converted to
the existing SPI-like scale and all 206 teams are ranked all-versus-all. Normal
production behavior is unseeded; separate seeded runs validate reproducibility.

## Names and application contract

`data/config/dictionary.csv` maps source aliases in the backend. The published
ranking must retain exactly the prior's 206 UI-compatible team names.

The validated ranking is copied byte-for-byte to:

- `ranking_final.csv`, read directly by `app/football_predictor.py`;
- `data/output/ranking_final.csv`;
- the dated ranking prior for the next stage.

The cumulative evidence output is likewise copied to the dated evidence prior
for the next stage. Publication happens only after validation and identical
ranking hashes are confirmed.

## Completed Stage 3 reference

The exact inputs, outputs, parameter comparison, warnings, mappings, and
validation evidence are under `data/output/stage3_2026_07_18/`. The concise
human-readable record is `VALIDATION_REPORT.md`; machine-readable checks are in
`validation.json`.
