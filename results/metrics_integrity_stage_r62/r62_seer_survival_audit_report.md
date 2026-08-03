# R6.2 Seer Survival Audit Report

## Data Sources

- R6.1 Seer game/action raw files for the original terminal-survival finding.
- R6.2 supplementary metric-audit replay for life-history reconstruction.

## Policy-Level Metrics

| Policy | Terminal Survival | One-Round Post-Reveal Survival | Next-Night Death Hazard |
|---|---:|---:|---:|
| delayed_round_2 | 0.000 | 0.000 | 0.007 |
| immediate_reveal | 0.000 | 0.020 | 0.665 |
| private_only | 0.000 | 0.000 | 0.000 |
| reveal_first_wolf | 0.000 | 0.000 | 0.484 |
| selective_useful_info | 0.000 | 0.000 | 0.495 |
| under_threat | 0.000 | 0.000 | 0.500 |

The terminal 0% value should be retained only with the precise label `terminal_survival_rate`, not as a generic survival rate.
