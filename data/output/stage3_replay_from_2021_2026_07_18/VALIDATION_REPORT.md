# Full 2021-to-Stage-3 replay validation

Status: PASSED AND PUBLISHED

The application ranking was rebuilt sequentially from the May 2021
FiveThirtyEight prior. Production Stage 1/Stage 2 football formulas and the
all-versus-all simulation were unchanged. Four-year equal-appearance evidence
pooling was applied at the Stage 2 and Stage 3 handoffs.

## Published ranking

- SHA-256: `88aff21cee6585e14b8ce313489b48ac05342b3cdc8bfe669d859fd47e3918e3`
- Teams: 206
- Top 10: Argentina, Spain, Brazil, France, Netherlands, England, Colombia,
  Italy, Germany, Belgium
- Stage 3 versus replayed January prior Spearman correlation: 0.997036
- Mean absolute Stage 3 rank movement: 3.0485
- Rwanda: 114; Ivory Coast: 42; Denmark: 13

The identical ranking is published to `ranking_final.csv`,
`data/output/ranking_final.csv`, and the dated 18 July 2026 prior.

## Sequential replay

| Stage | Window | Eligible | Friendly | World Cup | Other competitive |
|---|---|---:|---:|---:|---:|
| Stage 1 | 2021-05-26–2025-05-26 | 4,292 | 1,037 | 64 | 3,191 |
| Stage 2 | 2025-05-27–2026-01-26 | 787 | 180 | 0 | 607 |
| Stage 3 | 2026-01-27–2026-07-18 | 377 | 194 | 102 | 81 |

Stage 3's last completed eligible match is 2026-07-15, so the next update
starts 2026-07-16. The unfinished July 18 and July 19 matches were not used.

Stage 1 reproduced the saved May 2025 ranking's 214-team set and top ten; rank
Spearman is above 0.999. Small metric differences are documented because the
frozen July results file is not the original May 2025 source snapshot.

The verified 206-team app universe was retained at the historical handoff.
French Guiana, Guam, Macau, Mongolia, Samoa, Tahiti, Tonga, and Tuvalu were not
reintroduced.

## Evidence arithmetic

The Stage 2 handoff retained 6,533 prior appearances and added 1,574, giving
8,107 appearances for 2022-01-27–2026-01-26. The Stage 3 handoff retained
7,010 and added 754, giving 7,764 for 2022-07-16–2026-07-15.

Each retained eligible team appearance has weight one. Older appearances have
weight zero. Prior and new xG/xGA are combined by each team's observed shares,
then both complete distributions are normalized before the unchanged
all-versus-all simulation.

This is a rolling confidence window, not a strict zero-memory model. Older
information can remain indirectly embedded in a carried prior. That represents
persistent institutions, development, financing, coaching practice, and
competence, while the window prevents old match volume from dominating
confidence forever.

## Parameters and checks

Exact values are in `parameter_comparison.csv`. Stage 2 and Stage 3 both used
rank-normalized strength 0.05–0.95, adjustment factor
0.33277777777777784, dynamism 0.025, cutoff 0.07/strength 0.113, defensive
anchor 3.784242871189775, and unchanged caps/floors. Their recalculated
corrected-xGA caps were 8.728654671646698 and 10.165230613969603.

All 25 machine checks passed, including exact counts, no duplicated or
malformed eligible matches, exact UI names, finite normalized metrics, exact
ledger arithmetic, zero-match relative-order preservation, and byte-identical
seeded simulations. Seeded SHA-256:
`22b2d9881ec459f371f594cd916fc1dcfee19c03b89e1ae7ea3a6495b1813d04`.

See `validation.json`, `run_manifest.json`, `warnings.csv`, stage logs, and the
comparison CSVs in this directory for machine-readable evidence.
