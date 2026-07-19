# Stage 4 validation report

Overall status: **FAIL**

The exact unchanged pipeline completed, but the candidate is not published because the two-match goal median changes the absolute xG/xGA scale from 1.0 to 2.5.

## Result

- Candidate top six: Argentina, Spain, Brazil, France, Netherlands, England.
- The 1% and 7% cutoff sensitivity files are byte-identical.
- The only failed gate is absolute-scale football plausibility.

## Failed gates

- **zero_match_relative_order**: 202 zero-match teams preserve independent offense and defense order
- **absolute_scale_plausibility**: two-match empirical goal median is 2.5 versus incoming median 1.0; this globally scales app xG/xGA and expected scores by about 2.5x

## Warnings

- The unchanged cap diagnostic returned NaN and is not consumed by calculate_xg_xga.py.
- The two results are user-confirmed; no upstream API snapshot or commit exists.
- Publication is blocked solely by the absolute-scale plausibility failure caused by a two-match empirical median.
