# R5 Financial Risk Metrics and Payoff Frontier Research Report

## Technical Summary

R5 applies financial-risk metric analogues to the frozen R4 payoff dataset. The
analysis uses player-game observations clustered by game and keeps the R4
manifest unchanged.

- R4 manifest hash: `eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd`
- Metric manifest hash: `4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf`
- Source game rows: 4000
- Player-game rows: 40000
- Payoff event rows used for decomposition only: 200660
- Validation status: True

These are empirical game-payoff analogues, not literal financial-market returns
or investment performance metrics.

## Role-Level Risk and Return

| Role | Mean | Volatility | Downside dev | Neg prob | Sharpe-like | Sortino-like | CVaR95-like loss |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hunter | -0.7512 | 1.3319 | 1.6257 | 0.7035 | -0.5640 | -0.4621 | 2.2675 |
| seer | -0.0798 | 1.2550 | 0.9170 | 0.7020 | -0.0636 | -0.0870 | 1.5201 |
| villager | -0.5717 | 1.0107 | 1.2333 | 0.7035 | -0.5657 | -0.4636 | 1.5710 |
| werewolf | 1.2095 | 1.4341 | 1.0049 | 0.2965 | 0.8434 | 1.2035 | 1.2716 |
| witch | -0.2890 | 1.2321 | 1.1117 | 0.7035 | -0.2346 | -0.2600 | 1.6376 |

The highest core expected payoff belongs to `werewolf`. The
highest payoff volatility belongs to `werewolf`. The largest
downside deviation belongs to `hunter`. The best core
Sharpe-like and Sortino-like ratios are `werewolf` and
`werewolf`, respectively.

## Strategy-Level Risk and Return

| Role | Strategy | Mean | Volatility | Sharpe-like | Sortino-like |
| --- | --- | --- | --- | --- | --- |
| hunter | reference_strategy_mix | -0.8576 | 1.3051 | -0.6572 | -0.5166 |
| hunter | seer_highest_suspicion | -0.8966 | 1.2358 | -0.7255 | -0.5529 |
| hunter | villager_random_vote | -0.8681 | 1.2854 | -0.6754 | -0.5356 |
| hunter | witch_conservative_poison | -0.7420 | 1.3346 | -0.5560 | -0.4595 |
| hunter | wolf_random_kill | -0.3916 | 1.4310 | -0.2737 | -0.2438 |
| seer | reference_strategy_mix | -0.1688 | 1.1666 | -0.1447 | -0.1871 |
| seer | seer_highest_suspicion | -0.2104 | 1.1658 | -0.1805 | -0.2303 |
| seer | villager_random_vote | -0.3206 | 1.0752 | -0.2982 | -0.3381 |
| seer | witch_conservative_poison | -0.0375 | 1.2294 | -0.0305 | -0.0435 |
| seer | wolf_random_kill | 0.3384 | 1.4977 | 0.2259 | 0.3516 |
| villager | reference_strategy_mix | -0.6304 | 0.9909 | -0.6362 | -0.5088 |
| villager | seer_highest_suspicion | -0.6722 | 0.9758 | -0.6889 | -0.5397 |
| villager | villager_random_vote | -0.7014 | 0.9362 | -0.7492 | -0.5637 |
| villager | witch_conservative_poison | -0.5686 | 1.0233 | -0.5556 | -0.4587 |
| villager | wolf_random_kill | -0.2861 | 1.0677 | -0.2680 | -0.2409 |
| werewolf | reference_strategy_mix | 1.3184 | 1.3742 | 0.9594 | 1.3994 |
| werewolf | seer_highest_suspicion | 1.3743 | 1.3512 | 1.0171 | 1.4435 |
| werewolf | villager_random_vote | 1.3998 | 1.3280 | 1.0541 | 1.5274 |
| werewolf | witch_conservative_poison | 1.2463 | 1.4150 | 0.8807 | 1.3418 |
| werewolf | wolf_random_kill | 0.7085 | 1.5753 | 0.4498 | 0.6077 |
| witch | reference_strategy_mix | -0.3471 | 1.1984 | -0.2897 | -0.3155 |
| witch | seer_highest_suspicion | -0.3835 | 1.1652 | -0.3291 | -0.3537 |
| witch | villager_random_vote | -0.3781 | 1.1725 | -0.3225 | -0.3502 |
| witch | witch_conservative_poison | -0.3134 | 1.2070 | -0.2596 | -0.2814 |
| witch | wolf_random_kill | -0.0231 | 1.3739 | -0.0168 | -0.0193 |

The highest-return strategy is not universally the highest risk-adjusted
strategy. R5 therefore reports frontier membership and dominated strategies
instead of a single universal best policy.

## Efficient Frontier

| Role | Strategy | Risk metric | Mean | Risk | Efficient | Dominated |
| --- | --- | --- | --- | --- | --- | --- |
| hunter | reference_strategy_mix | standard_deviation | -0.8576 | 1.3051 | True | False |
| hunter | seer_highest_suspicion | standard_deviation | -0.8966 | 1.2358 | True | False |
| hunter | villager_random_vote | standard_deviation | -0.8681 | 1.2854 | True | False |
| hunter | witch_conservative_poison | standard_deviation | -0.7420 | 1.3346 | True | False |
| hunter | wolf_random_kill | standard_deviation | -0.3916 | 1.4310 | True | False |
| seer | reference_strategy_mix | standard_deviation | -0.1688 | 1.1666 | True | False |
| seer | seer_highest_suspicion | standard_deviation | -0.2104 | 1.1658 | True | False |
| seer | villager_random_vote | standard_deviation | -0.3206 | 1.0752 | True | False |
| seer | witch_conservative_poison | standard_deviation | -0.0375 | 1.2294 | True | False |
| seer | wolf_random_kill | standard_deviation | 0.3384 | 1.4977 | True | False |
| villager | reference_strategy_mix | standard_deviation | -0.6304 | 0.9909 | True | False |
| villager | seer_highest_suspicion | standard_deviation | -0.6722 | 0.9758 | True | False |
| villager | villager_random_vote | standard_deviation | -0.7014 | 0.9362 | True | False |
| villager | witch_conservative_poison | standard_deviation | -0.5686 | 1.0233 | True | False |
| villager | wolf_random_kill | standard_deviation | -0.2861 | 1.0677 | True | False |
| werewolf | reference_strategy_mix | standard_deviation | 1.3184 | 1.3742 | False | True |
| werewolf | seer_highest_suspicion | standard_deviation | 1.3743 | 1.3512 | False | True |
| werewolf | villager_random_vote | standard_deviation | 1.3998 | 1.3280 | True | False |
| werewolf | witch_conservative_poison | standard_deviation | 1.2463 | 1.4150 | False | True |
| werewolf | wolf_random_kill | standard_deviation | 0.7085 | 1.5753 | False | True |
| witch | reference_strategy_mix | standard_deviation | -0.3471 | 1.1984 | True | False |
| witch | seer_highest_suspicion | standard_deviation | -0.3835 | 1.1652 | True | False |
| witch | villager_random_vote | standard_deviation | -0.3781 | 1.1725 | True | False |
| witch | witch_conservative_poison | standard_deviation | -0.3134 | 1.2070 | True | False |
| witch | wolf_random_kill | standard_deviation | -0.0231 | 1.3739 | True | False |

Efficient strategies are non-dominated within role and payoff specification.
Dominated strategies have at least one alternative with no lower expected payoff
and no higher risk.

## Information and Manipulation Premiums

Core information premium for the Seer:
`1.2651`.

Core manipulation premium for wolves:
`2.7245`.

Both are association metrics based on R4 attribution flags. They should not be
read as causal estimates.

## Core Versus Extended Payoff Specification

Extended payoff adds survival, exposure, deception, credibility, and observable
opportunity-cost components. R5 keeps core and extended specifications separate
and flags conclusions that move across specifications as sensitivity-dependent.

## Coefficient Sensitivity

R5 reuses the R4 coefficient sensitivity grid at 0.75x, 1.00x, and 1.25x
without mutating the baseline manifest. Rank correlations and top-condition
changes are reported in `r5_coefficient_sensitivity_summary.csv`.

## Required R5 Questions

1. Expected payoff by role is shown in the role table.
2. Payoff volatility by role is shown in the role table.
3. Downside deviation by role is shown in the role table.
4. Negative-payoff probability by role is shown in the role table.
5. 90% and 95% VaR-like thresholds are in `r5_role_var_cvar_summary.csv`.
6. 90% and 95% CVaR-like values are in `r5_role_var_cvar_summary.csv`.
7. Sharpe-like ratios by role are in the role table.
8. Sortino-like ratios by role are in the role table.
9. Highest expected payoff role: `werewolf`.
10. Best risk-adjusted core role: `werewolf` by Sharpe-like and `werewolf` by Sortino-like.
11. Worst downside-risk role: `hunter`.
12. Highest expected-payoff strategy within each role is in `r5_strategy_risk_return_summary.csv`.
13. Best Sharpe-like strategy within each role is in `r5_strategy_risk_return_summary.csv`.
14. Best Sortino-like strategy within each role is in `r5_strategy_risk_return_summary.csv`.
15. Efficient frontier strategies are in `r5_strategy_frontier_summary.csv`.
16. Strictly dominated strategies are in `r5_dominated_strategy_summary.csv`.
17. Highest-return strategy does not always have the highest risk-adjusted return.
18. Seer information premium is `1.2651` in the core specification.
19. Wolf manipulation premium is `2.7245` in the core specification.
20. Opportunity-cost adjustment does not double-count R4 opportunity cost and reconciles to total payoff.
21. Seed stability is summarized in `r5_seed_robustness.csv`.
22. Regime stability is summarized in `r5_regime_robustness.csv`.
23. Core/extended stability is summarized in `r5_core_vs_extended_summary.csv`.
24. Coefficient sensitivity is summarized in `r5_coefficient_sensitivity_summary.csv`.
25. Robust conclusions are those whose rank signs and frontier status remain stable.
26. Fragile conclusions are those that move under specification or coefficient sensitivity.
27. Leakage and double-counting checks passed in R5 validation.
28. Historical data are not sufficient for all strategy comparisons.
29. The financial analogy is quantitatively useful as a game-payoff risk language, not as a literal market claim.
30. The project is ready for R6 synthesis.

## Limitations

R5 relies on the R4 validation dataset for complete event-level attribution.
Earlier aggregate experiments often lack the role/action ledger needed for full
historical payoff reconstruction.

## Next Hypothesis

R6 should test whether role-specific strategy recommendations remain coherent
when expected payoff, downside risk, risk-adjusted payoff, and robustness are
synthesized jointly.
