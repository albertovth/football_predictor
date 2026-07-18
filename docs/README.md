# Ranking documentation

This directory contains the authoritative documentation for the national-team
ranking currently used by the application.

## Start here for the next update

Use [STAGE4_UPDATE_GUIDE.md](STAGE4_UPDATE_GUIDE.md). It gives the exact prior
files, next start date, calibration order, commands, outputs, and validation
gates for extending the validated Stage 3 ranking.

Supporting references:

- [METHODS.md](METHODS.md) explains the current method and the distinction
  between raw new-period xG/xGA and cumulative evidence stabilization.
- `pipeline/spi_stage3/README.md` documents the Stage 3 evidence scripts.
- `data/output/stage3_2026_07_18/VALIDATION_REPORT.md` records the completed
  Stage 3 run, parameters, match counts, mappings, and reproducibility checks.

## Authority rules

- The application reads the repository-root `ranking_final.csv`.
- The published Stage 3 prior pair for the next update is
  `data/config/priors/spi_global_rankings_intl_18_7_2026.csv` and
  `data/config/priors/ranking_evidence_18_7_2026.csv`.
- `pipeline/spi_stage2/` remains the production formula and simulation engine;
  its directory name does not mean that an old prior or old parameters are
  reused.
- `pipeline/spi_stage3/` adds cumulative evidence weighting without
  reimplementing the Stage 2 adjusted-goal formulas.
- Do not use `archive/`, `post_world_cup_update.py`, `wrong_output`, or any
  post-World-Cup custom updater. Those are not valid production paths.

The obsolete `post_world_cup_2026_calibration.md` was removed because it
described the rejected custom implementation and could not reproduce the
published Stage 3 result.
