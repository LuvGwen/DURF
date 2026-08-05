# R8.2 Targeted Independent Replication Report

## Technical Summary

R8.2 is a targeted independent replication of three load-bearing role recommendations identified by R8.1. The stage uses a fresh R8.2 seed namespace (820-839), 1000 matched sets per module, and only two frozen policy arms per module. Hunter and Werewolf are not replicated in this stage.

## Frozen Policy Summary

| Module | Policy | Games | Village Win | Wolf Win | Mean Actor Payoff | Actor Payoff 95% CI | SD | Sharpe-like |
|---|---|---:|---:|---:|---:|---|---:|---:|
| villager | reference | 1000 | 0.2890 | 0.7110 | -0.3402 | [-0.3998, -0.2807] | 0.9611 | -0.3540 |
| villager | trust_weighted | 1000 | 0.3580 | 0.6420 | -0.1873 | [-0.2505, -0.1242] | 1.0191 | -0.1838 |
| seer | private_only | 1000 | 0.2860 | 0.7140 | -0.2652 | [-0.3241, -0.2064] | 0.9501 | -0.2792 |
| seer | immediate_reveal | 1000 | 0.3180 | 0.6820 | -0.1979 | [-0.2585, -0.1373] | 0.9783 | -0.2023 |
| witch | reference | 1000 | 0.2860 | 0.7140 | -0.2102 | [-0.2704, -0.1499] | 0.9715 | -0.2163 |
| witch | aggressive_full | 1000 | 0.3570 | 0.6430 | -0.0451 | [-0.1121, 0.0220] | 1.0819 | -0.0416 |

## Preregistered Contrasts

| Module | Outcome Role | Metric | Candidate | Mean Diff | 95% CI | Raw p | Holm p | Effect Size dz | Label |
|---|---|---|---|---:|---|---:|---:|---:|---|
| villager | primary | actor_payoff | trust_weighted | 0.1529 | [0.0914, 0.2144] | 0.0020 | 0.0060 | 0.1542 | replicated positive effect |
| seer | primary | actor_payoff | immediate_reveal | 0.0673 | [0.0237, 0.1110] | 0.6234 | 0.6234 | 0.0957 | positive but not statistically replicated |
| witch | primary | actor_payoff | aggressive_full | 0.1651 | [0.0981, 0.2321] | 0.0030 | 0.0060 | 0.1526 | replicated positive effect |
| villager | secondary | village_win | trust_weighted | 0.0690 | [0.0399, 0.0981] | 0.2867 | 0.8601 | 0.1470 | positive but not statistically replicated |
| seer | secondary | village_win | immediate_reveal | 0.0320 | [0.0103, 0.0537] | 0.7882 | 0.8601 | 0.0912 | positive but not statistically replicated |
| witch | secondary | village_win | aggressive_full | 0.0710 | [0.0404, 0.1016] | 0.2907 | 0.8601 | 0.1437 | positive but not statistically replicated |

## Replication Decisions

| Module | Candidate | Primary Diff | Holm p | Seed Support | Regime Support | Decision |
|---|---|---:|---:|---:|---:|---|
| villager | trust_weighted | 0.1529 | 0.0060 | 0.9000 | 0.8000 | replicated positive effect |
| seer | immediate_reveal | 0.0673 | 0.6234 | 0.8500 | 0.6000 | positive but not statistically replicated |
| witch | aggressive_full | 0.1651 | 0.0060 | 0.8000 | 0.9000 | replicated positive effect |

## Role-Specific Diagnostics

| Module | Policy | Metric Summary |
|---|---|---|
| villager | reference | total_votes=20780; correct_vote_count=7262; wrong_vote_count=13518; correct_vote_rate=0.3495; wrong_eliminations=1814 |
| villager | trust_weighted | total_votes=21108; correct_vote_count=8483; wrong_vote_count=12625; correct_vote_rate=0.4019; wrong_eliminations=1685 |
| seer | immediate_reveal | first_check_wolf_rate=0.3330; found_wolf_by_check_2_rate=0.4910; found_wolf_by_check_3_rate=0.4930; mean_checks_until_first_wolf=1.3286; no_wolf_found_rate=0.5070; mean_wolves_discovered=0.5500; seer_survival_rate=0.0000; mean_total_seer_checks=1.6570; mean_search_path_coverage=0.1841; total_seer_reveals=1657 |
| seer | private_only | first_check_wolf_rate=0.3330; found_wolf_by_check_2_rate=0.4830; found_wolf_by_check_3_rate=0.4830; mean_checks_until_first_wolf=1.3106; no_wolf_found_rate=0.5170; mean_wolves_discovered=0.5380; seer_survival_rate=0.0000; mean_total_seer_checks=1.6340; mean_search_path_coverage=0.1816; total_seer_reveals=0 |
| witch | aggressive_full | total_witch_saves=1000; total_witch_poison=788; total_night_kills_prevented=1000; mean_witch_saves_per_game=1.0000; mean_witch_poison_per_game=0.7880 |
| witch | reference | total_witch_saves=859; total_witch_poison=302; total_night_kills_prevented=859; mean_witch_saves_per_game=0.8590; mean_witch_poison_per_game=0.3020 |

## Validation

- PASS: expected_game_row_count (6000)
- PASS: action_rows_present (51644)
- PASS: frozen_modules_only (seer,villager,witch)
- PASS: frozen_policy_pairs_only ([('seer', 'immediate_reveal'), ('seer', 'private_only'), ('villager', 'reference'), ('villager', 'trust_weighted'), ('witch', 'aggressive_full'), ('witch', 'reference')])
- PASS: no_hunter_or_werewolf_replication (hunter/wolf absent from R8.2 game rows)
- PASS: r82_seed_namespace_independent (r82=820-839 r61=520-539)
- PASS: game_ids_unique (6000)
- PASS: matched_seat_assignments_within_module (0)
- PASS: primary_outcome_fixed (actor_payoff)
- PASS: manifest_hashes_authoritative (R4=eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd; R5=4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf)

## Conclusion

R8.2 completed the frozen targeted independent replication with the preregistered actor-payoff primary outcome. Replication labels above determine whether the R8.1 load-bearing recommendations are supported independently.
