# R5.1 Strategy Attribution Audit

## Technical Summary

R5.1 separates actor-specific strategies from global configurations and
cross-role externalities. `wolf_random_kill` may affect Hunter, Seer, Witch, and
Villager payoffs, but those rows are externalities and must not be reported as
strategies those roles can choose.

## Mapping Counts

- Invalid actor-specific recommendations removed: `32`
- Valid actor-specific role-strategy pairs: `4`
- Cross-role externality records: `24800`
- Suspected cross-join rows: `0`

## Corrected Actor-Specific Metrics

| Role | Actor Strategy | Mean | Sharpe-like | Sortino-like | Downside |
| --- | --- | --- | --- | --- | --- |
| seer | seer_highest_suspicion | -0.2104 | -0.1805 | -0.2303 | 0.9133 |
| villager | villager_random_vote | -0.7014 | -0.7492 | -0.5637 | 1.2443 |
| werewolf | wolf_random_kill | 0.7085 | 0.4498 | 0.6077 | 1.1659 |
| witch | witch_conservative_poison | -0.3134 | -0.2596 | -0.2814 | 1.1138 |
