# R8.3 Seer Statistical Consistency Report

## Finding

The R8.2 Seer paired actor-payoff CI was reproducible, but the R8.2 Seer
raw and Holm-adjusted p-values were not. The discrepancy was caused by a
sign-flip implementation error: zero matched differences were removed and
the null mean denominator was changed from all 1,000 matched sets to only
the nonzero subset.

## Corrected Authoritative Result

- Difference: 0.06735
- Matched-set bootstrap CI: [0.02379875, 0.11055]
- Corrected raw p-value: 0.003399830008499575
- Corrected Holm-adjusted p-value: 0.003399830008499575
- Result: replicated_positive_primary_effect

## Interpretation

The Seer effect is statistically replicated on the preregistered actor-payoff
primary outcome after correction. However, final default policy wording must
still separate payoff evidence from safety evidence because R8.2 did not export
next-night death hazard or short-horizon survival fields, while R6.2 documented
post-reveal exposure for `immediate_reveal`.
