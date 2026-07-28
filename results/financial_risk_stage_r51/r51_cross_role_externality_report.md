# R5.1 Cross-Role Externality Report

## Summary

R5 condition labels remain useful for externality analysis. They answer how one
role's policy shift changes another role's payoff under matched R4 validation
games.

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

These rows are descriptive cross-role payoff externalities, not strategy
recommendations for the affected role.
