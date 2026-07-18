# Stage 3 evidence update

Stage 3 keeps the production Stage 2 football calculations unchanged and adds
one explicit stabilization step between raw xG/xGA calculation and the existing
all-versus-all simulation.

The direct Stage 2 replacement calculation gave two new matches the power to
replace a complete prior rating. That caused sparse-sample jumps. Stage 3
instead applies this calculation separately to xG and xGA:

    scaled prior xG =
        (team prior xG / median prior xG) * empirical median goals

    scaled prior xGA =
        (team prior xGA / median prior xGA) * empirical median goals

    pooled metric =
        (scaled prior metric * prior matches + new metric * new matches)
        / (prior matches + new matches)

The new metric is based only on matches in the new stage window. Prior xG/xGA
are transferred by their relative position in the prior distributions, not
treated as absolute goal values. The pooled 206-team xG and xGA distributions
are independently normalized to the empirical median goals. The existing Stage
2 simulation then consumes them without modification.

Prior matches are the cumulative eligible-match evidence supporting the
incoming prior. For Stage 3, build_prior_evidence.py reconstructs them from
Stage 1 plus Stage 2. Later updates use the total carried in evidence_final.csv,
so Stage 4 does not recount the history.

This is a new confidence layer, not a claim that the original Stage 2 script
performed a formal Bayesian update. Adjusted-goal formulas, high/low branches,
friendly weighting, opponent corrections, floors, the hard cap of 6, the xGA
percentile cap, and simulation remain the production Stage 2 implementation.

Scripts:

- build_prior_evidence.py: one-time reconstruction of the incoming Stage 3
  evidence counts.
- combine_prior_evidence.py: scales the prior, combines evidence, normalizes all
  206 teams, writes confederation inputs, and carries evidence forward.

See docs/STAGE4_UPDATE_GUIDE.md for the complete commands and validation gates.
