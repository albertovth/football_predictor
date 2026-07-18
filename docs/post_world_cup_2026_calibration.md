# Post-World-Cup 2026 Ranking Update

This update uses `data/config/priors/spi_global_rankings_intl_pre_world_cup_2026.csv`, whose final included source result is 26 January 2026 (Uzbekistan 2-2 China PR). The update window begins 27 January 2026.

The current snapshot contains 400 completed source matches, of which 377 are eligible: 194 friendlies, 102 World Cup matches, and 81 other competitive matches. Friendlies apply the existing 0.5 goal weight before metric calculation. Twenty-three records are excluded and documented in `data/input/post_world_cup_2026/excluded_matches.csv`; mapping decisions are recorded in `name_mapping_audit.csv`.

The 7% low-team cutoff is retained because the existing calibration diagnostic found no candidate quantile satisfying its documented criterion in this sample. The resulting internal threshold is 0.113. Other prior-dependent values are recalculated by the update module; the current calibration is in `data/output/post_world_cup_2026/calibration.json`.

Teams with no eligible observations are carried forward by preserving their relative prior offensive and defensive positions, then mapping those values onto the new phase median-goal scale. They are not silently dropped.

The output is provisional as of 18 July 2026. France-England (third-place match) and Spain-Argentina (final) were not yet played and are intentionally absent. After results are available, rebuild the input snapshot and run:

```bash
python scripts/build_post_world_cup_2026_matches.py ...
python scripts/run_post_world_cup_2026_update.py ... --publish
```

The staged root `ranking_final.csv` and `data/output/ranking_final.csv` are the provisional ranking used by the application.
