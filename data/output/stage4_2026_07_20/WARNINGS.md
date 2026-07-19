# Stage 4 warnings and resolved issues

- Resolved: the first isolated candidate used the two-match median (2.5); it was rejected and never published.
- Resolved: all Stage 4 normalization now uses the rolling four-year median (1.0).
- Cutoff: 1% selected; 7% sensitivity is byte-identical.
- Cap helper: NaN on two matches, diagnostic only; production caps remain 6.
- No unresolved mapping, duplicate, malformed-score, missing-prior, unfinished-match, or excluded-record issue remains.
