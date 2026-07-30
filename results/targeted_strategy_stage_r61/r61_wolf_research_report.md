# R6.1 Wolf Targeted Strategy Report

## Technical Summary

This module tests 6 wolf policies in 1000 matched sets per policy. The independent unit is the matched complete game. 2 primary contrasts reached Holm-adjusted 0.05 significance.

## Policy Summary

| Policy | Village Win | Wolf Win | Mean Actor Payoff | SD | CVaR95 | Sharpe-like |
|---|---:|---:|---:|---:|---:|---:|
| reference | 0.292 | 0.708 | 0.697 | 0.946 | -0.868 | 0.7366 |
| aggressive_false_accuse | 0.340 | 0.660 | 0.594 | 0.991 | -0.885 | 0.5993 |
| aggressive_kill_restrained_deception | 0.333 | 0.667 | 0.606 | 0.989 | -0.887 | 0.6131 |
| threat_adaptive | 0.292 | 0.708 | 0.697 | 0.946 | -0.868 | 0.7366 |
| deep_cover | 0.594 | 0.406 | 0.083 | 1.034 | -0.888 | 0.0804 |
| minimal_deception | 0.346 | 0.654 | 0.595 | 1.001 | -0.889 | 0.5943 |

## Primary Contrasts

| Candidate | Metric | Mean Diff | CI Low | CI High | Raw p | Holm p | Label |
|---|---|---:|---:|---:|---:|---:|---|
| aggressive_false_accuse | actor_payoff | -0.1030 | -0.1587 | -0.0473 | 0.0709 | 0.2128 | promising but uncertain |
| aggressive_kill_restrained_deception | actor_payoff | -0.0907 | -0.1474 | -0.0340 | 0.0899 | 0.2128 | promising but uncertain |
| threat_adaptive | actor_payoff | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | no meaningful improvement |
| deep_cover | actor_payoff | -0.6139 | -0.6921 | -0.5356 | 0.0010 | 0.0050 | statistically supported harmful effect |
| minimal_deception | actor_payoff | -0.1018 | -0.1791 | -0.0246 | 0.0150 | 0.0599 | promising but uncertain |
| aggressive_false_accuse | wolf_win | -0.0480 | -0.0746 | -0.0214 | 0.4995 | 1.0000 | promising but uncertain |
| aggressive_kill_restrained_deception | wolf_win | -0.0410 | -0.0681 | -0.0139 | 0.5854 | 1.0000 | promising but uncertain |
| threat_adaptive | wolf_win | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 | no meaningful improvement |
| deep_cover | wolf_win | -0.3020 | -0.3395 | -0.2645 | 0.0010 | 0.0050 | statistically supported harmful effect |
| minimal_deception | wolf_win | -0.0540 | -0.0908 | -0.0172 | 0.3097 | 1.0000 | promising but uncertain |

## Role-Specific Diagnostics

Role-specific diagnostic summaries are exported in the module summary CSV files. The best expected-payoff policy in this run is `reference`.

## Validation

- Game IDs are unique.
- Initial randomized seat-role assignment is matched across policy arms.
- R6.1 policy flags are experimental and default to False.

## Limitations

This is a pilot-scale R6.1 matched live validation at the minimum allowed 1,000 matched sets per module. Strategy rows are complete-game outcomes; action raw rows are diagnostic and are not treated as independent games.
