# R5.1 Actor-Specific Strategy Report

## Corrected Within-Role Strategy Results

Only rows where `strategy_owner_role == affected_role` are included in the
primary actor-specific analysis.

| Role | Actor Strategy | Mean | Sharpe-like | Sortino-like | Downside |
| --- | --- | --- | --- | --- | --- |
| seer | seer_highest_suspicion | -0.2104 | -0.1805 | -0.2303 | 0.9133 |
| villager | villager_random_vote | -0.7014 | -0.7492 | -0.5637 | 1.2443 |
| werewolf | wolf_random_kill | 0.7085 | 0.4498 | 0.6077 | 1.1659 |
| witch | witch_conservative_poison | -0.3134 | -0.2596 | -0.2814 | 1.1138 |

## Formal Matched Contrasts Against Reference

| Role | Strategy | Mean Diff | CI Low | CI High | Raw p | Holm p | Matched Sets |
| --- | --- | --- | --- | --- | --- | --- | --- |
| villager | villager_random_vote | -0.0710 | -0.2034 | 0.0613 | 0.6820 | 0.6820 | 400 |
| seer | seer_highest_suspicion | -0.0416 | -0.1980 | 0.1233 | 0.6295 | 0.6295 | 400 |
| witch | witch_conservative_poison | 0.0338 | -0.1363 | 0.2046 | 0.3794 | 0.3794 | 400 |
| werewolf | wolf_random_kill | -0.6099 | -0.8057 | -0.4107 | 0.0000 | 0.0000 | 400 |

Because the R4 validation design contains one directly controlled non-reference
strategy for each of Werewolf, Seer, Witch, and Villager, corrected frontiers are
sparse. Hunter has no actor-specific R4 strategy condition and therefore no
primary R5.1 strategy recommendation.
