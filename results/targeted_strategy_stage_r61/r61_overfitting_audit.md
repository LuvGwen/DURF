# R6.1 Overfitting Audit

R6.1 uses matched complete-game live validation to close the five role-specific strategy gaps identified in R6. It preserves default simulator behavior behind disabled experimental flags and treats action-level rows as diagnostics only.

| Module | Policies | Best Mean Actor-Payoff Policy |
|---|---:|---|
| hunter | 6 | reference |
| seer | 6 | immediate_reveal |
| witch | 6 | aggressive_full |
| wolf | 6 | reference |
| villager | 6 | trust_weighted |

See the module reports and CSV outputs for confidence intervals, Holm-adjusted p-values, risk metrics, and robustness tables.
