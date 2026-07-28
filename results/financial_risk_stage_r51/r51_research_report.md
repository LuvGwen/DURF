# R5.1 Role-Strategy Attribution Audit Report

## Technical Summary

R5.1 finds that the surprising R5 strategy recommendations were not a payoff
formula failure. The issue was attribution: R5 strategy labels were global
configuration labels copied to every player in a game. R5.1 corrects this by
separating actor-specific strategies from cross-role externalities.

## Corrected Actor-Specific Results

| Role | Actor Strategy | Mean | Sharpe-like | Sortino-like | Downside |
| --- | --- | --- | --- | --- | --- |
| seer | seer_highest_suspicion | -0.2104 | -0.1805 | -0.2303 | 0.9133 |
| villager | villager_random_vote | -0.7014 | -0.7492 | -0.5637 | 1.2443 |
| werewolf | wolf_random_kill | 0.7085 | 0.4498 | 0.6077 | 1.1659 |
| witch | witch_conservative_poison | -0.3134 | -0.2596 | -0.2814 | 1.1138 |

## Formal Contrasts

| Role | Strategy | Mean Diff | CI Low | CI High | Raw p | Holm p | Matched Sets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| villager | villager_random_vote | -0.0710 | -0.2034 | 0.0613 | 0.6820 | 0.6820 | 400 |
| seer | seer_highest_suspicion | -0.0416 | -0.1980 | 0.1233 | 0.6295 | 0.6295 | 400 |
| witch | witch_conservative_poison | 0.0338 | -0.1363 | 0.2046 | 0.3794 | 0.3794 | 400 |
| werewolf | wolf_random_kill | -0.6099 | -0.8057 | -0.4107 | 0.0000 | 0.0000 | 400 |

## Cross-Role Externalities

| Affected Role | Owner | External Strategy | Mean Diff | CI Low | CI High |
| --- | --- | --- | --- | --- | --- |
| hunter | seer | seer_highest_suspicion | -0.0390 | -0.2074 | 0.1351 |
| hunter | villager | villager_random_vote | -0.0105 | -0.1866 | 0.1755 |
| hunter | werewolf | wolf_random_kill | 0.4660 | 0.2836 | 0.6512 |
| hunter | witch | witch_conservative_poison | 0.1156 | -0.0625 | 0.2994 |
| seer | villager | villager_random_vote | -0.1519 | -0.3078 | 0.0051 |
| seer | werewolf | wolf_random_kill | 0.5071 | 0.3266 | 0.6769 |
| seer | witch | witch_conservative_poison | 0.1313 | -0.0290 | 0.2979 |
| villager | seer | seer_highest_suspicion | -0.0418 | -0.1105 | 0.0210 |
| villager | werewolf | wolf_random_kill | 0.3443 | 0.2755 | 0.4111 |
| villager | witch | witch_conservative_poison | 0.0619 | -0.0131 | 0.1336 |
| werewolf | seer | seer_highest_suspicion | 0.0559 | -0.0512 | 0.1654 |
| werewolf | villager | villager_random_vote | 0.0814 | -0.0261 | 0.1883 |
| werewolf | witch | witch_conservative_poison | -0.0722 | -0.1878 | 0.0440 |
| witch | seer | seer_highest_suspicion | -0.0364 | -0.1993 | 0.1276 |
| witch | villager | villager_random_vote | -0.0310 | -0.1945 | 0.1316 |
| witch | werewolf | wolf_random_kill | 0.3240 | 0.1471 | 0.4927 |

## Premium Analyses

| Definition | Exposed | Comparison | Diff | CI Low | CI High | Status |
| --- | --- | --- | --- | --- | --- | --- |
| primary_useful_information | 576 | 1424 | 1.2651 | 1.1429 | 1.3772 | causal estimate unavailable |
| wolf_found_by_check | 994 | 1006 | 0.9539 | 0.8525 | 1.0553 | causal estimate unavailable |
| villager_confirmation | 1699 | 301 | -0.5583 | -0.7305 | -0.3944 | causal estimate unavailable |

| Definition | Exposed | Comparison | Diff | CI Low | CI High | Warning |
| --- | --- | --- | --- | --- | --- | --- |
| primary_any_manipulation | 1989 | 11 | 2.7245 | 2.6626 | 2.7870 | weak comparison overlap |
| coordinated_vote_or_village_elimination | 1913 | 87 | 2.5923 | 2.5265 | 2.6582 | weak comparison overlap |
| special_target_elimination | 1970 | 30 | 1.6543 | 1.0957 | 2.1618 | weak comparison overlap |
| successful_deception | 1169 | 831 | 0.6231 | 0.4866 | 0.7510 |  |

## Required Final Questions

1. R5 reported `wolf_random_kill` as best for non-wolf roles because
   `condition_name` was grouped as a global game configuration.
2. This was a labelling/interpretation issue, not a Cartesian-product coding bug.
3. Role-level R5 metrics remain valid.
4. R5 strategy frontiers and dominated-strategy claims are superseded.
5. Corrected owners are listed in `r51_corrected_strategy_registry.csv`.
6. Valid Villager strategy: `villager_random_vote`.
7. Valid Seer strategy: `seer_highest_suspicion`.
8. Valid Witch strategy: `witch_conservative_poison`.
9. Valid Hunter strategy: none in the R4 validation design.
10. Valid Werewolf strategy: `wolf_random_kill`.
11-14. Corrected rankings are sparse because each eligible role has one direct
strategy.
15. Actor-specific frontiers contain only direct strategies.
16. No actor-specific strategies are strictly dominated in R5.1 because no role
has multiple direct strategies in this validation dataset.
17. Matched contrasts against reference exist for Werewolf, Seer, Witch, and
Villager.
18. Cross-role strategy effects remain descriptive externalities.
19. Holm-adjusted results are reported in
`r51_actor_specific_primary_contrasts.csv`.
20-21. Leave-one-seed and leave-one-regime outputs are complete.
22. Cross-role externalities are reported separately.
23-24. Premium group sizes and CIs are reported.
25. Manipulation-group imbalance is severe.
26. The primary useful-information label is outcome-dependent.
27. No gameplay leakage checks failed.
28. No R5.1 mapping tests failed.
29. R6 readiness: `ready for synthesis`.
30. Exact R6 synthesis: unified role strategy optimization using corrected
actor-specific rows, externality labels, and evidence-quality flags.

## R6 Readiness

Strategy ownership is explicit, externalities are separated, leave-one-out robustness and premium CIs are reported.
