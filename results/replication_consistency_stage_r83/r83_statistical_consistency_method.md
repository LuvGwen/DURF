# R8.3 Statistical Consistency Method

R8.3 reads only frozen R8.2 complete-game outputs. The inference block is
`matched_set_id`; no player rows or action rows are treated as independent
primary observations.

For each frozen role module, R8.3 computes candidate-minus-reference paired
actor-payoff differences. The confidence interval is a matched-set cluster
bootstrap percentile interval over the paired differences. The raw p-value is
a two-sided Monte Carlo sign-flip test over all matched differences, including
zeros. Holm correction is then applied across exactly the three frozen primary
tests: Villager, Seer, and Witch.

The R8.2 inconsistency was traced to a sign-flip helper that removed zero
differences and computed null means over the nonzero subset. Removing zeros is
not itself harmful if the denominator remains the full matched-set count, but
changing the denominator inflates the null variance and can make p-values
inconsistent with a positive paired CI.
