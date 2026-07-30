# R6.1 Witch Targeted Strategy Report

## Technical Summary

This module tests 6 witch policies in 1000 matched sets per policy. The independent unit is the matched complete game. 2 primary contrasts reached Holm-adjusted 0.05 significance.

## Policy Summary

| Policy | Village Win | Wolf Win | Mean Actor Payoff | SD | CVaR95 | Sharpe-like |
|---|---:|---:|---:|---:|---:|---:|
| reference | 0.301 | 0.699 | -0.168 | 0.998 | -1.077 | -0.1688 |
| aggressive_full | 0.352 | 0.648 | -0.037 | 1.087 | -1.117 | -0.0343 |
| save_aggressive_poison_conservative | 0.318 | 0.682 | -0.162 | 0.957 | -0.900 | -0.1691 |
| save_conservative_poison_aggressive | 0.274 | 0.726 | -0.312 | 1.055 | -1.350 | -0.2955 |
| conservative_full | 0.201 | 0.799 | -0.494 | 0.844 | -1.050 | -0.5856 |
| risk_balanced | 0.311 | 0.689 | -0.179 | 0.970 | -1.057 | -0.1845 |

## Primary Contrasts

| Candidate | Metric | Mean Diff | CI Low | CI High | Raw p | Holm p | Label |
|---|---|---:|---:|---:|---:|---:|---|
| aggressive_full | actor_payoff | 0.1312 | 0.0663 | 0.1961 | 0.0190 | 0.0569 | promising but uncertain |
| save_aggressive_poison_conservative | actor_payoff | 0.0066 | -0.0501 | 0.0634 | 0.9131 | 1.0000 | no meaningful improvement |
| save_conservative_poison_aggressive | actor_payoff | -0.1434 | -0.2140 | -0.0728 | 0.0070 | 0.0280 | statistically supported harmful effect |
| conservative_full | actor_payoff | -0.3256 | -0.3859 | -0.2653 | 0.0010 | 0.0050 | statistically supported harmful effect |
| risk_balanced | actor_payoff | -0.0105 | -0.0735 | 0.0526 | 0.8501 | 1.0000 | no meaningful improvement |
| aggressive_full | village_win | 0.0510 | 0.0216 | 0.0804 | 0.4396 | 1.0000 | promising but uncertain |
| save_aggressive_poison_conservative | village_win | 0.0170 | -0.0099 | 0.0439 | 0.7652 | 1.0000 | no meaningful improvement |
| save_conservative_poison_aggressive | village_win | -0.0270 | -0.0586 | 0.0046 | 0.6144 | 1.0000 | no meaningful improvement |
| conservative_full | village_win | -0.1000 | -0.1280 | -0.0720 | 0.1429 | 0.7143 | promising but uncertain |
| risk_balanced | village_win | 0.0100 | -0.0206 | 0.0406 | 0.8492 | 1.0000 | no meaningful improvement |

## Role-Specific Diagnostics

Role-specific diagnostic summaries are exported in the module summary CSV files. The best expected-payoff policy in this run is `aggressive_full`.

## Validation

- Game IDs are unique.
- Initial randomized seat-role assignment is matched across policy arms.
- R6.1 policy flags are experimental and default to False.

## Limitations

This is a pilot-scale R6.1 matched live validation at the minimum allowed 1,000 matched sets per module. Strategy rows are complete-game outcomes; action raw rows are diagnostic and are not treated as independent games.
