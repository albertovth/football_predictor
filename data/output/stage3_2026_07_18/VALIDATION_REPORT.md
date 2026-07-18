# Stage 3 validation report

Status: PASSED

The app ranking was updated only after 66 of 66 automated checks and all 16
repository tests passed.

## Published result

- Ranking SHA-256:
  ffd346a5d512d6754885f35207ebc17ff9155363f7ec199e5ec548371dccebb1
- Teams: 206
- Top 10: Spain, England, France, Switzerland, Argentina, Colombia,
  South Korea, Brazil, Senegal, Norway
- Prior-to-new Spearman rank correlation: 0.997660842796693
- Mean absolute rank change: 2.7475728155339807
- Median absolute rank change: 2
- Largest rise: 13 places
- Largest fall: 19 places

| Team | Prior | New | Movement |
|---|---:|---:|---:|
| Argentina | 6 | 5 | +1 |
| Spain | 1 | 1 | 0 |
| England | 2 | 2 | 0 |
| France | 3 | 3 | 0 |
| Japan | 34 | 21 | +13 |
| Ivory Coast | 47 | 37 | +10 |
| Rwanda | 160 | 153 | +7 |

The rejected direct-replacement result is preserved in
audit/rejected_new_only and is not used by the app.

## Exact prior and dates

- Prior: data/output/stage3_2026_07_18/prior_ranking.csv
- Prior SHA-256:
  a773aef99836f50ec32cf6f858c0da1b47aec1cfaef2fb22165abb44f649c87a
- Prior teams: 206
- Prior top three: Spain, England, France
- Prior last included completed match: 2026-01-26
- Configured Stage 3 start: 2026-01-27
- First actual eligible Stage 3 match: 2026-02-25
- Last completed eligible match included: 2026-07-15
- Source cutoff: 2026-07-18

France-England on July 18 and Spain-Argentina on July 19 were unfinished and
not processed. The next update therefore starts on July 16.

## Frozen input

- File: data/input/stage3_2026_07_18/results.csv
- SHA-256:
  9bb7ae6bac69e6d028ecd1a2c3a040d8590671bc430ccf8ac17f4ad3d1a126ee
- Source rows in the cutoff window: 401
- Completed source rows: 400
- Unfinished source rows: 1
- Eligible rows: 377
- Friendlies: 194
- World Cup matches: 102
- Other competitive matches: 81
- Excluded completed rows: 23
- Duplicate completed rows: 0
- Duplicate eligible rows: 0
- Malformed completed scores: 0

All excluded rows and reasons are in audit/excluded_matches.csv. No mapped prior
country was silently removed.

## Team-name validation

The backend retained source names and the simulation mapped them to the
existing UI names. Aliases encountered were:

- Cape Verde to Cape Verde Islands
- China to China PR
- Curaçao to Curacao
- DR Congo to Congo DR
- Republic of Ireland to Rep of Ireland
- Saint Kitts and Nevis to St. Kitts and Nevis
- Saint Lucia to St. Lucia
- Saint Martin to St. Martin
- Saint Vincent and the Grenadines to St. Vincent and the Grenadines
- United States to USA
- United States Virgin Islands to US Virgin Islands

The result contains exactly the prior's 206 UI names.

## Stage 2 recalibration

The current prior SPI was rank-normalized to the interval 0.05 through 0.95.

| Parameter | Prior Stage 2 | Stage 3 raw |
|---|---:|---:|
| Prior teams | 214 | 206 |
| Observed teams | 206 | 178 |
| Minimum strength | 0.05 | 0.05 |
| Median strength | 0.5 | 0.5 |
| Maximum strength | 0.95 | 0.95 |
| Cutoff quantile | 0.07 | 0.07 |
| Cutoff strength | 0.113 | 0.113 |
| Adjustment factor | 0.33277777777777784 | 0.33277777777777784 |
| Dynamism | 0.025 | 0.025 |
| Low-team defensive P_c | 3.784242871189775 | 3.784242871189775 |
| Adjusted-goal cap | 6 | 6 |
| Minimum offensive reward | 0.01 | 0.01 |
| Defensive penalty cap | 6 | 6 |
| Corrected xGA percentile | 0.95 | 0.95 |
| Corrected xGA cap | 8.728654671646698 | 8.396484358315535 |
| Corrected xG median | 3.507346571355047 | 3.7030226644707422 |
| Clipped xGA median | 3.044190894413699 | 2.9596064068731396 |
| Empirical median goals | 1 | 1 |
| Offensive scale | 0.28511582179164424 | 0.27004965689102145 |
| Defensive scale | 0.32849451124601586 | 0.3378827663292269 |
| Carried zero-match teams | 0 | 28 |

The cap helper printed 1.5316205533596838 offense and 2.0833333333333335
defense. These are diagnostics: unchanged calculate_xg_xga.py does not consume
them and retains its literal cap of 6. An isolated no-cap probe was rejected
because it was less stable.

The unchanged cutoff search tested 1 percent through 25 percent and found no
qualifying cutoff. The documented 7 percent fallback was retained, giving
cutoff strength 0.113.

## Cumulative evidence calibration

Old goals were not reprocessed. Eligible counts only quantify confidence in the
incoming prior.

- Stage 1 eligible matches in the recount: 4,292
- Stage 1 appearances assigned to the current 206 teams: 8,461
- Saved Stage 2 appearances: 1,574
- Incoming prior evidence appearances: 10,035
- Stage 3 appearances: 754
- Evidence appearances carried into Stage 4: 10,789
- Minimum prior weight: 0.830508
- Median prior weight: 0.934409
- Maximum prior weight: 1.0

Argentina used 67 prior appearances and 11 new matches, for prior weight
0.858974. Rwanda used 38 prior appearances and two new matches, for prior weight
0.95.

Pre-normalization medians were 1.0103094166918365 xG and 1.007826250155126
xGA. Both final distributions were normalized to 1.0.

## Regression and reproducibility

- Recreated prior offense and defense maximum errors: below 1e-12
- Empty-window offense and defense maximum errors: below 1e-12
- Zero-new-match teams: 28
- Their xG and xGA relative-order correlations: effectively 1.0
- Seeded run SHA-256:
  0f37da7a55d5b60b54015b38087fa0a9a192d0eb86e139e973be2f7b865ee97d
- Second seeded run: byte-identical
- Production run: unseeded, preserving existing behavior
- Seeded and unseeded top-10 order: identical

Machine-readable checks are in candidate/validation.json. Exact parameters are
in candidate/parameters.json and candidate/parameter_comparison.csv.

## Published files

- ranking_final.csv
- data/output/ranking_final.csv
- data/output/stage3_2026_07_18/ranking_final.csv
- data/config/priors/spi_global_rankings_intl_18_7_2026.csv
- data/output/ranking_evidence.csv
- data/config/priors/ranking_evidence_18_7_2026.csv
