# Current national-team ranking method

Status: authoritative for the validated Stage 4 ranking published on
2026-07-20. For operational commands for the next update, use
`docs/STAGE4_UPDATE_GUIDE.md`.

## Pipeline history

- Stage 1 started from the May 2021 FiveThirtyEight international SPI prior and
  processed matches from 2021-05-26 through 2025-05-26.
- Stage 2 used the replayed Stage 1 result as its prior, processed matches from
  2025-05-27 through 2026-01-26, and pooled prior and new relative xG/xGA by
  rolling team-appearance evidence before simulation.
- Stage 3 used that replayed 206-team Stage 2 result, processed matches from
  2026-01-27, and applied the same evidence pooling. The last eligible
  completed match in the frozen source was 2026-07-15.
- Stage 4 used that published Stage 3 ranking as its prior and processed France
  4-6 England on 2026-07-18 and Spain 1-0 Argentina on 2026-07-19. The updated
  rolling evidence and goal-median window is 2022-07-20 through 2026-07-19.

This is a full sequential replay from the May 2021 starting prior, not one
single formula applied to every match. Each stage recalculates its raw window;
the later handoffs combine prior and new relative xG/xGA by evidence.

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

Raw xG and xGA are calculated only from eligible matches in the new update
window. Old matches are not reprocessed to create the new-period
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
10. Derive corrected metric medians and scale offense and defense to the raw
    empirical goal median from the rolling four-year results window.
11. Write raw xG/xGA and confederation inputs.

The labels xG and xGA are goal- and opponent-adjusted team metrics; they are
not shot-event expected-goal models.

## Relative prior transfer and evidence weighting

An incoming prior's xG and xGA are not treated as permanent absolute goal
values. They are first expressed relative to their respective prior
distributions and transferred to the new period's empirical median-goal scale:

```text
scaled prior xG =
    (team prior xG / median prior xG) * rolling empirical median goals

scaled prior xGA =
    (team prior xGA / median prior xGA) * rolling empirical median goals
```

For a team with new matches, each metric is then combined independently:

```text
pooled metric =
    (scaled prior metric * prior evidence appearances
     + raw new-period metric * new-period appearances)
    / (prior evidence appearances + new-period appearances)
```

The complete 206-team pooled xG and xGA distributions are then independently
normalized to the rolling empirical median goals. The median source and dated
evidence ledger share one inclusive four-year window. Automated updates derive
its start as the run date minus four years plus one day.

This distinction is important:

- A team's raw new-period metric is based only on its new matches.
- Prior evidence counts control confidence in its incoming relative position;
  they do not cause old goals to be recalculated.
- A team with few new matches moves modestly because both sources are weighted.
- A team with no new matches has new weight zero and therefore preserves its
  relative prior xG and xGA positions on the new scale.

The replay applies the dated four-year ledger at both the Stage 2 and Stage 3
handoffs. Every retained appearance has weight one and older appearances have
weight zero. There is no fitted decay, multiplier, or pseudo-count.

The new-period share is therefore empirical match share. Four new appearances
against 36 retained prior appearances contribute `4 / 40`, or 10 percent. The
four-year boundary is the explicit one-World-Cup-cycle policy; chronological
holdout testing found it effectively tied with cumulative pooling and strongly
better than direct replacement.

The boundary limits confidence, not all historical memory. Earlier information
can remain embedded in the carried prior, representing persistent football
institutions and competence; new observed appearances progressively dilute it.

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

The evidence aggregate and dated ledger are likewise copied to the next
stage's prior files. Publication happens only after validation and identical
ranking hashes are confirmed.

## Completed Stage 4 reference

The exact inputs, outputs, parameter comparison, warnings, mappings, and
validation evidence are under `data/output/stage4_2026_07_20/`. The concise
human-readable record is `VALIDATION_REPORT.md`; machine-readable checks are in
`validation.json`.
