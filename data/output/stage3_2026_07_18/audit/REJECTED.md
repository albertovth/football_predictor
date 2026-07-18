# Rejected Stage 3 attempt

This output must not be used by the app or as a future prior.

Reason: Face-validity failure caused by replacing prior off/def with one- or two-match Stage 3 samples for observed teams; Rwanda ranked fifth from two clean sheets.

The live application ranking was restored from prior_ranking.csv.

- Restored live SHA-256: a773aef99836f50ec32cf6f858c0da1b47aec1cfaef2fb22165abb44f649c87a
- Rejected ranking SHA-256: 4f7346dea700e42f08c2ec7cc8dbc381a158320ac8c031c7e906e88cb0cfd297
- Evidence: Rwanda had two eligible matches, both clean sheets, producing xGA 0.0036687482572823 and rank 5.
- Root cause: the unchanged Stage 2 metric code replaces prior off/def for every observed team instead of shrinking or combining the new sample with the prior.
