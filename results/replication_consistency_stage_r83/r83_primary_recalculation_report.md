# R8.3 Primary Contrast Recalculation Report

R8.3 recomputes the three frozen R8.2 primary contrasts from `r82_game_level_raw.csv`, using `matched_set_id` as the inference block. The mean paired differences match R8.2 exactly. The authoritative p-values are corrected matched sign-flip p-values that retain zero differences in the denominator.

Bootstrap replicates: 10000.
Sign-flip replicates: 20000.

| Module | Candidate | Difference | Bootstrap 95% CI | Raw p | Holm p | Result |
|---|---|---:|---|---:|---:|---|
| villager | trust_weighted | 0.1529 | [0.0919, 0.2154] | 0.0000 | 0.0001 | replicated_positive_primary_effect |
| seer | immediate_reveal | 0.0673 | [0.0238, 0.1105] | 0.0034 | 0.0034 | replicated_positive_primary_effect |
| witch | aggressive_full | 0.1651 | [0.0977, 0.2326] | 0.0000 | 0.0001 | replicated_positive_primary_effect |
