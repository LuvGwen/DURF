# R4 Unified Role-Specific Payoff Matrix Research Report

## Technical Summary

R4 implemented a versioned role-specific payoff manifest, event-level payoff
ledger, deterministic payoff recalculation, historical coverage audit, and
validation dataset. Default gameplay remains unchanged: the R4 ledger is
disabled unless `enable_r4_payoff_ledger=True`, and the main validation runner
computes payoff as analysis-only post-processing.

- Validation games: 2000
- Independent seeds: 10
- Behavioral regimes: 5
- Player-role observations: 40000
- Payoff event rows: 200660
- Manifest hash: `eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd`
- Validation status: True

## Key Findings With Evidence

### Core Role Payoff Summary

| role | mean total | median | negative payoff probability | mean terminal | mean action |
| --- | --- | --- | --- | --- | --- |
| hunter | -0.751 | -1.300 | 0.704 | -0.488 | -0.263 |
| seer | -0.080 | -0.750 | 0.702 | -0.488 | 0.409 |
| villager | -0.572 | -1.050 | 0.704 | -0.407 | -0.165 |
| werewolf | 1.209 | 2.033 | 0.296 | 0.611 | 0.000 |
| witch | -0.289 | -0.900 | 0.704 | -0.488 | 0.199 |

The core specification is dominated by terminal team payoff, as intended. Role
action components add interpretable differences without replacing win/loss as
the main source of payoff.

### Core And Extended Specifications Are Separated

The extended specification adds survival, exposure, deception, credibility, and
observable opportunity-cost terms. It is reported as sensitivity analysis and is
not used as the primary R4 conclusion.

### Historical Recalculation Is Limited By Missing Event Logs

Most historical CSV files are partially recalculable because they preserve game
or strategy summaries rather than full event-level role/action histories. R4
therefore documents coverage instead of inventing missing events.

## Scope, Data, And Metric Definitions

The independent unit is a complete game. The validation dataset uses 10 seeds,
five behavioral regimes, five strategy conditions, and eight games per
seed-regime-condition cell. Both core and extended payoff specifications are
calculated for every game.

`total_payoff = terminal_team_payoff + individual_action_payoff +
shared_wolf_team_bonus + survival_or_exposure_payoff + opportunity_cost`.

## Methodology

Payoff is calculated from completed game event logs. Terminal team payoff is
separate from immediate event payoff. Shared wolf events are split equally
across wolves so a team-level event is not multiplied by the number of wolves.
Confidence intervals use bootstrap resampling over player-role observations for
descriptive uncertainty; R4 does not make a Sharpe-like risk-adjusted claim.

## Required R4 Questions

1. Was a unified role-specific payoff matrix implemented? Yes.
2. What are the final core payoff values? See `r4_role_payoff_matrix.csv`.
3. Which values match the proposal exactly? Team wins, seer investigation,
witch correct save/poison, hunter correct/wrong shot, and wolf shared anchors.
4. Which values differ from the proposal? Symmetric loss values and conservative
vote-shaping terms are R4 design choices.
5. Why were any values changed? To separate terminal loss, action rewards, and
minimal voting accuracy without over-shaping.
6. How are team and individual payoff separated? Separate ledger categories.
7. How are immediate and terminal payoff separated? Each component declares
`immediate_or_terminal`.
8. How is opportunity cost defined? Only observable rule-based states are used.
9. How is survival risk defined? Extended-only `survives_game` and exposure
costs.
10. How is exposure risk defined? Extended-only credibility and accusation
costs.
11. How is seer information attribution defined? Checked wolf eliminated by day
vote within two rounds.
12. How is a correct witch save defined? Antidote saves a village-team night
target who would otherwise die.
13. How is a correct hunter shot defined? Legal death shot targets a wolf.
14. How are wolf team rewards distributed? Equal split across all wolves.
15. Were any double-counting risks found? Yes, documented in the audit.
16. How were they resolved? Core excludes duplicated correlated terms or splits
team rewards.
17. Which historical datasets were fully recalculable? None of the targeted
historical summary CSVs are fully event-recalculable.
18. Which were partially recalculable? Most aggregate experiment outputs.
19. Which require regeneration? Sources without event-level rows.
20. What is mean payoff by role? See `r4_role_payoff_summary.csv`.
21. What is median payoff by role? See `r4_role_payoff_summary.csv`.
22. What is negative-payoff probability by role? See
`r4_negative_payoff_probability.csv`.
23. Which strategy has the highest mean payoff within each role? See
`r4_strategy_payoff_comparison.csv`.
24. Are strategy rankings stable across seeds? See `r4_seed_robustness.csv`.
25. Are strategy rankings stable across regimes? See
`r4_regime_robustness.csv`.
26. Are rankings stable under 0.75x and 1.25x sensitivity? See
`r4_payoff_sensitivity_analysis.csv`.
27. Does the core specification produce reasonable payoff distributions? Yes;
validation reconciles all player and game totals.
28. Does the extended specification change conclusions? It changes component
decomposition and is reported separately.
29. Did any leakage checks fail? No.
30. Is the payoff system ready for R5 risk-adjusted analysis? Yes; R5 should now
add variance and Sharpe-like metrics.

## Limitations, Uncertainty, And Robustness

Historical recalculation is limited by missing full event logs in older
experiments. Bootstrap intervals are descriptive and do not convert event rows
into independent games. Strategy comparisons are compact validation comparisons,
not a full re-run of every historical experiment.

## Recommended Next Step

Proceed to R5: Financial Risk Metrics and Sharpe-Like Payoff Analysis.
