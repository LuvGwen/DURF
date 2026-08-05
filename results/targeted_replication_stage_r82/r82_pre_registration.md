# R8.2 Targeted Independent Replication Pre-Registration

## Frozen Scope

R8.2 independently replicates only three load-bearing role recommendations:

1. Villager `reference` versus `trust_weighted`
2. Seer `private_only` versus `immediate_reveal`
3. Witch `reference` versus `aggressive_full`

Hunter and Werewolf replication are explicitly excluded. No additional
strategies, threshold searches, interim sample-size changes, or post-hoc
primary outcome changes are allowed in this stage.

## Independent Sampling Plan

- Seeds: 820-839 (20 seeds)
- Behavioral regimes: 10 frozen R6.1 regimes
- Replicates per seed-regime cell: 5
- Matched sets per module: 1000
- Policy arms per module: 2
- Total complete-game rows: 6000

## Outcomes

The preregistered primary outcome is `actor_payoff` for all three role
modules. The secondary outcome is `village_win`. Primary conclusions
must be based on the primary actor-payoff contrast, with Holm correction across
the three frozen primary contrasts.

## Manifest Integrity

The authoritative R4 payoff manifest hash is `eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd`. The
authoritative R5 metric manifest hash is `4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf`. R8.2 does
not modify either manifest.
