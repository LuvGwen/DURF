# R5.1 Root Cause Report

## Finding

R5 did not show evidence of a Cartesian-product coding bug. The root cause is
that R5 grouped payoff rows by `condition_name` and affected role. In the R4
validation dataset, `condition_name` is a global rollout configuration label:
all players in a game inherit the same condition label, even when only one role
controls the changed policy.

## Interpretation

- Coding/data bug: no join bug found.
- Valid but incorrectly interpreted: yes. R5 strategy-condition rows are valid
  as global condition and cross-role externality estimates.
- R5 outputs that remain valid: role-level metrics, role-level rankings,
  seed robustness, regime robustness, coefficient sensitivity, and frozen
  financial metric definitions.
- R5 outputs superseded by R5.1: actor-specific strategy rankings, strategy
  frontiers, and dominated-strategy claims.
- Raw R5 data regeneration required: no. R5.1 can reconstruct valid actor and
  externality views from the existing R4/R5 rows.
