# R6.1 Villager Targeted Strategy Report

## Technical Summary

This module tests 6 villager policies in 1000 matched sets per policy. The independent unit is the matched complete game. 2 primary contrasts reached Holm-adjusted 0.05 significance.

## Policy Summary

| Policy | Village Win | Wolf Win | Mean Actor Payoff | SD | CVaR95 | Sharpe-like |
|---|---:|---:|---:|---:|---:|---:|
| reference | 0.291 | 0.709 | -0.338 | 0.961 | -1.041 | -0.3524 |
| random_vote | 0.230 | 0.770 | -0.473 | 0.877 | -1.038 | -0.5391 |
| suspicion_only | 0.293 | 0.707 | -0.331 | 0.970 | -1.044 | -0.3410 |
| p_wolf_only | 0.240 | 0.760 | -0.446 | 0.907 | -1.040 | -0.4919 |
| trust_weighted | 0.402 | 0.598 | -0.094 | 1.043 | -1.023 | -0.0901 |
| guarded_herding | 0.334 | 0.666 | -0.244 | 0.999 | -1.038 | -0.2444 |

## Primary Contrasts

| Candidate | Metric | Mean Diff | CI Low | CI High | Raw p | Holm p | Label |
|---|---|---:|---:|---:|---:|---:|---|
| random_vote | actor_payoff | -0.1343 | -0.2126 | -0.0559 | 0.0020 | 0.0080 | statistically supported harmful effect |
| suspicion_only | actor_payoff | 0.0076 | -0.0593 | 0.0746 | 0.8651 | 0.8651 | no meaningful improvement |
| p_wolf_only | actor_payoff | -0.1078 | -0.1672 | -0.0485 | 0.0330 | 0.0989 | promising but uncertain |
| trust_weighted | actor_payoff | 0.2445 | 0.1820 | 0.3070 | 0.0010 | 0.0050 | statistically supported improvement |
| guarded_herding | actor_payoff | 0.0942 | 0.0416 | 0.1468 | 0.0859 | 0.1718 | promising but uncertain |
| random_vote | village_win | -0.0610 | -0.0982 | -0.0238 | 0.2298 | 0.9191 | promising but uncertain |
| suspicion_only | village_win | 0.0020 | -0.0296 | 0.0336 | 0.9530 | 1.0000 | no meaningful improvement |
| p_wolf_only | village_win | -0.0510 | -0.0792 | -0.0228 | 0.5045 | 1.0000 | promising but uncertain |
| trust_weighted | village_win | 0.1110 | 0.0813 | 0.1407 | 0.0909 | 0.4545 | promising but uncertain |
| guarded_herding | village_win | 0.0430 | 0.0180 | 0.0680 | 0.5465 | 1.0000 | promising but uncertain |

## Role-Specific Diagnostics

Role-specific diagnostic summaries are exported in the module summary CSV files. The best expected-payoff policy in this run is `trust_weighted`.

## Validation

- Game IDs are unique.
- Initial randomized seat-role assignment is matched across policy arms.
- R6.1 policy flags are experimental and default to False.

## Limitations

This is a pilot-scale R6.1 matched live validation at the minimum allowed 1,000 matched sets per module. Strategy rows are complete-game outcomes; action raw rows are diagnostic and are not treated as independent games.
