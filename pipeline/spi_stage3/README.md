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

The published ranking was replayed from the May 2021 starting prior. The dated
four-year ledger was applied at both the Stage 2 and Stage 3 handoffs. It
expires older appearance counts; every retained appearance has weight one and
there is no decay coefficient or pseudo-count.

The rule was checked on 240 chronologically held-out matches. Four-year and
cumulative pooling were effectively tied, while direct new-period replacement
was materially worse. Four years is therefore documented as the bounded
one-World-Cup-cycle policy, not claimed as an optimized duration.

This is a confidence layer, not a claim that the original Stage 2 script
performed a formal Bayesian update. Adjusted-goal formulas, high/low branches,
friendly weighting, opponent corrections, floors, the hard cap of 6, the xGA
percentile cap, and simulation remain the production Stage 2 implementation.

The four-year boundary limits confidence rather than erasing all inherited
memory. Older information may remain embedded in a carried prior, reflecting
persistent football institutions and competence, and is diluted by new
appearances.

Scripts:

- build_prior_evidence.py: retained helper for reconstructing the original
  cumulative Stage 3 evidence audit; it is not the current rolling method.
- build_evidence_window.py: reconstructs the dated four-year ledger used at
  the replayed Stage 2 and Stage 3 handoffs and carried into Stage 4.
- combine_prior_evidence.py: scales the prior, combines evidence, normalizes all
  206 teams, writes confederation inputs, expires old ledger rows, and carries
  the dated evidence forward.

The current run outputs are under
`data/output/stage3_replay_from_2021_2026_07_18/`. The older
`data/output/stage3_2026_07_18/` directory is a superseded historical audit.
See `docs/STAGE4_UPDATE_GUIDE.md` for the next commands and validation gates.
