# R8.3 Pre-Registration

R8.3 is a replication statistical consistency audit and final role-conclusion
freeze. It reads only frozen R8.2/R8.1/R6.2 artifacts.

## Frozen Comparisons

- Villager: `trust_weighted` vs `reference`
- Seer: `immediate_reveal` vs `private_only`
- Witch: `aggressive_full` vs `reference`

## Primary Outcome

The primary outcome is actor payoff. The independent inference block is
`matched_set_id`. Holm correction is applied across exactly the three primary
role contrasts.

## Fixed Methods

- Matched-set bootstrap replicates: 10000
- Matched sign-flip replicates: 20000
- No gameplay regeneration
- No threshold tuning
- No post-hoc primary outcome changes
- No reconstruction of unavailable lifecycle metrics

## Frozen Manifest Hashes

- R4 payoff manifest: `eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd`
- R5 metric manifest: `4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf`
