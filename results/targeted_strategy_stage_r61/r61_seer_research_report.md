# R6.1 Seer Targeted Strategy Report

## Technical Summary

This module tests 6 seer policies in 1000 matched sets per policy. The independent unit is the matched complete game. No primary contrast reached Holm-adjusted 0.05 significance.

## Policy Summary

| Policy | Village Win | Wolf Win | Mean Actor Payoff | SD | CVaR95 | Sharpe-like |
|---|---:|---:|---:|---:|---:|---:|
| private_only | 0.301 | 0.699 | -0.235 | 0.961 | -1.000 | -0.2448 |
| immediate_reveal | 0.337 | 0.663 | -0.159 | 0.993 | -1.000 | -0.1602 |
| reveal_first_wolf | 0.310 | 0.690 | -0.215 | 0.971 | -1.000 | -0.2220 |
| delayed_round_2 | 0.313 | 0.687 | -0.211 | 0.974 | -1.000 | -0.2161 |
| under_threat | 0.303 | 0.697 | -0.231 | 0.963 | -1.000 | -0.2398 |
| selective_useful_info | 0.309 | 0.691 | -0.218 | 0.969 | -1.000 | -0.2244 |

## Primary Contrasts

| Candidate | Metric | Mean Diff | CI Low | CI High | Raw p | Holm p | Label |
|---|---|---:|---:|---:|---:|---:|---|
| immediate_reveal | actor_payoff | 0.0762 | 0.0327 | 0.1198 | 0.6174 | 1.0000 | promising but uncertain |
| reveal_first_wolf | actor_payoff | 0.0198 | -0.0123 | 0.0519 | 0.9780 | 1.0000 | no meaningful improvement |
| delayed_round_2 | actor_payoff | 0.0248 | -0.0001 | 0.0496 | 0.8831 | 1.0000 | no meaningful improvement |
| under_threat | actor_payoff | 0.0043 | -0.0013 | 0.0100 | 1.0000 | 1.0000 | no meaningful improvement |
| selective_useful_info | actor_payoff | 0.0177 | -0.0141 | 0.0496 | 0.9001 | 1.0000 | no meaningful improvement |
| immediate_reveal | village_win | 0.0360 | 0.0143 | 0.0577 | 0.6354 | 1.0000 | promising but uncertain |
| reveal_first_wolf | village_win | 0.0090 | -0.0070 | 0.0250 | 1.0000 | 1.0000 | no meaningful improvement |
| delayed_round_2 | village_win | 0.0120 | -0.0004 | 0.0244 | 0.8701 | 1.0000 | no meaningful improvement |
| under_threat | village_win | 0.0020 | -0.0008 | 0.0048 | 0.4945 | 1.0000 | no meaningful improvement |
| selective_useful_info | village_win | 0.0080 | -0.0079 | 0.0239 | 0.8881 | 1.0000 | no meaningful improvement |

## Role-Specific Diagnostics

Role-specific diagnostic summaries are exported in the module summary CSV files. The best expected-payoff policy in this run is `immediate_reveal`.

## Validation

- Game IDs are unique.
- Initial randomized seat-role assignment is matched across policy arms.
- R6.1 policy flags are experimental and default to False.

## Limitations

This is a pilot-scale R6.1 matched live validation at the minimum allowed 1,000 matched sets per module. Strategy rows are complete-game outcomes; action raw rows are diagnostic and are not treated as independent games.
