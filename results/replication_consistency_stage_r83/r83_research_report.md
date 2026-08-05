# R8.3 Replication Consistency Audit and Final Role Freeze

## Summary

R8.3 found that the R8.2 Seer CI/p-value inconsistency was caused by a reporting/calculation error in the sign-flip p-value denominator. The R8.2 paired actor-payoff differences and CIs were reproducible, but the raw p-values were recomputed using all matched-set differences.

## Corrected Primary Contrasts

| Module | Candidate | Difference | 95% CI | Raw p | Holm p | Result |
|---|---|---:|---|---:|---:|---|
| villager | trust_weighted | 0.1529 | [0.0919, 0.2154] | 0.0000 | 0.0001 | replicated_positive_primary_effect |
| seer | immediate_reveal | 0.0673 | [0.0238, 0.1105] | 0.0034 | 0.0034 | replicated_positive_primary_effect |
| witch | aggressive_full | 0.1651 | [0.0977, 0.2326] | 0.0000 | 0.0001 | replicated_positive_primary_effect |

## Final Role Conclusions

| Role | Final Evidence Label | Recommendation |
|---|---|---|
| Villager | independently_replicated_confirmatory_supported | Recommend trust_weighted within tested simulation configuration. |
| Seer | replicated_positive_with_material_tradeoff | Retain private_only as safety-conservative default; treat immediate_reveal as payoff-supported but exposure-constrained. |
| Witch | replicated_positive_with_material_tradeoff | Use aggressive_full only as a conditional risk-tolerant policy; retain reference as conservative default option. |

## Five-Role Recommendation Freeze

| Role | Conservative Default | Performance Policy | Evidence Grade |
|---|---|---|---|
| Villager | reference | trust_weighted | A |
| Seer | private_only | immediate_reveal | B |
| Witch | reference | aggressive_full | A/B |
| Hunter | reference | reference | B |
| Werewolf | reference | reference / threat_adaptive family | B |

## Witch Tradeoff

Aggressive full improves expected Witch actor payoff and village win rate under the frozen payoff specification, while increasing wrong-poison rate by 0.2466. Primary and extended potion waste remain unavailable from the R8.2 export.

## Seer Safety Evidence

R8.3 separates corrected R8.2 payoff replication from historical R6.2 lifecycle safety evidence. R8.2 did not export next-night hazard or short-horizon survival fields, so immediate reveal is payoff-supported but exposure-constrained rather than a safety-superior default.

## R9 Readiness

Decision: **READY FOR R9 WITH AUDITED LIMITATIONS**.
