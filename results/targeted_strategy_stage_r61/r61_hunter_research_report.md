# R6.1 Hunter Targeted Strategy Report

## Technical Summary

This module tests 6 hunter policies in 1000 matched sets per policy. The independent unit is the matched complete game. 2 primary contrasts reached Holm-adjusted 0.05 significance.

## Policy Summary

| Policy | Village Win | Wolf Win | Mean Actor Payoff | SD | CVaR95 | Sharpe-like |
|---|---:|---:|---:|---:|---:|---:|
| reference | 0.305 | 0.695 | -0.414 | 1.070 | -1.403 | -0.3868 |
| random_shot | 0.251 | 0.749 | -0.575 | 1.005 | -1.405 | -0.5719 |
| no_shot | 0.217 | 0.783 | -0.559 | 0.853 | -1.103 | -0.6548 |
| highest_suspicion | 0.305 | 0.695 | -0.414 | 1.070 | -1.403 | -0.3868 |
| highest_p_wolf | 0.303 | 0.697 | -0.439 | 1.062 | -1.365 | -0.4130 |
| conservative_threshold | 0.222 | 0.778 | -0.551 | 0.870 | -1.137 | -0.6334 |

## Primary Contrasts

| Candidate | Metric | Mean Diff | CI Low | CI High | Raw p | Holm p | Label |
|---|---|---:|---:|---:|---:|---:|---|
| random_shot | actor_payoff | -0.1608 | -0.2307 | -0.0909 | 0.0809 | 0.2428 | promising but uncertain |
| no_shot | actor_payoff | -0.1448 | -0.1999 | -0.0897 | 0.0010 | 0.0050 | statistically supported harmful effect |
| highest_suspicion | actor_payoff | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | no meaningful improvement |
| highest_p_wolf | actor_payoff | -0.0250 | -0.0718 | 0.0218 | 0.8521 | 1.0000 | no meaningful improvement |
| conservative_threshold | actor_payoff | -0.1375 | -0.1919 | -0.0831 | 0.0020 | 0.0080 | statistically supported harmful effect |
| random_shot | village_win | -0.0540 | -0.0825 | -0.0255 | 0.4496 | 1.0000 | promising but uncertain |
| no_shot | village_win | -0.0880 | -0.1134 | -0.0626 | 0.2557 | 1.0000 | promising but uncertain |
| highest_suspicion | village_win | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | no meaningful improvement |
| highest_p_wolf | village_win | -0.0020 | -0.0208 | 0.0168 | 0.9171 | 1.0000 | no meaningful improvement |
| conservative_threshold | village_win | -0.0830 | -0.1081 | -0.0579 | 0.2787 | 1.0000 | promising but uncertain |

## Role-Specific Diagnostics

Role-specific diagnostic summaries are exported in the module summary CSV files. The best expected-payoff policy in this run is `reference`.

## Validation

- Game IDs are unique.
- Initial randomized seat-role assignment is matched across policy arms.
- R6.1 policy flags are experimental and default to False.

## Limitations

This is a pilot-scale R6.1 matched live validation at the minimum allowed 1,000 matched sets per module. Strategy rows are complete-game outcomes; action raw rows are diagnostic and are not treated as independent games.
