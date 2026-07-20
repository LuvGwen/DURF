# Structured Seer Search Statistical Analysis Report

## Technical Summary

The structured seer search experiment analyzed 35,000 game-level rows from 14 strategies, 5 seeds, and 500 games per strategy-seed cell. A seed-adjusted logistic model found an overall strategy effect on village victory (LR=118.69, df=13, p=3.649e-19). Descriptively, `alternate_sides` had the highest village win rate (44.16%) and `right_to_left` was close behind (43.88%), compared with random (40.52%). However, the specific `alternate_sides` vs `right_to_left` contrast was not statistically supported after correction, so `alternate_sides` should be treated as descriptively highest rather than proven best.

The clearest negative result is that behavioral exploitation strategies underperformed: `highest_p_wolf` and `highest_suspicion` had lower village win rates than random, with corrected pairwise evidence against both. Their early wolf discovery rates were not better than random, and their seer survival rates were lower, suggesting that aggressive behavioral targeting narrows the search without improving information quality in this simulation.

## Scope, Data, and Metrics

- Primary dataset: `results/structured_seer_search/structured_seer_search_game_level_raw.csv`.
- Unit of analysis: one completed game.
- Outcome: `village_win`, a binary indicator for village victory.
- Main baseline: `random` seer checking.
- Seed handling: seed fixed effects in primary logistic models.
- Search-path coverage: `unique_checked_targets / 9`.
- Inference note: strategy is pre-treatment; early discovery, seer survival, coverage, and diversity are intermediate or post-treatment variables. Mechanism models are diagnostic, not formal causal mediation.

## Descriptive Results

The top descriptive strategy was `alternate_sides`, followed by `right_to_left` and `farthest_first`. `random` and `default` matched because the structured experiment enables the repeat guard for both.

| strategy | village win | 95% CI | first check wolf | found by check 3 | no wolf found | seer survival | coverage |
|---|---:|---:|---:|---:|---:|---:|---:|
| random | 40.52% | 38.61%-42.46% | 34.72% | 63.60% | 33.76% | 30.32% | 0.29 |
| default | 40.52% | 38.61%-42.46% | 34.72% | 63.60% | 33.76% | 30.32% | 0.29 |
| edge_first | 41.44% | 39.52%-43.38% | 34.20% | 65.76% | 32.04% | 30.80% | 0.29 |
| inner_first | 42.08% | 40.16%-44.03% | 31.48% | 63.00% | 34.24% | 31.44% | 0.29 |
| highest_p_wolf | 34.88% | 33.04%-36.77% | 32.44% | 63.12% | 34.96% | 28.84% | 0.29 |
| highest_suspicion | 34.84% | 33.00%-36.73% | 33.56% | 62.28% | 35.40% | 26.12% | 0.29 |
| left_to_right | 40.84% | 38.93%-42.78% | 33.72% | 63.44% | 33.60% | 31.00% | 0.29 |
| right_to_left | 43.88% | 41.95%-45.83% | 33.28% | 64.36% | 33.28% | 33.68% | 0.30 |
| alternate_sides | 44.16% | 42.22%-46.11% | 33.24% | 63.28% | 33.40% | 31.72% | 0.29 |
| nearest_first | 41.68% | 39.76%-43.62% | 33.16% | 64.60% | 32.80% | 31.48% | 0.30 |
| farthest_first | 42.88% | 40.95%-44.83% | 32.20% | 62.80% | 34.28% | 31.32% | 0.29 |
| coverage_balanced | 41.28% | 39.36%-43.22% | 33.92% | 64.68% | 33.12% | 30.60% | 0.29 |
| hybrid_suspicion_position | 36.84% | 34.97%-38.75% | 32.88% | 63.72% | 33.92% | 29.88% | 0.29 |
| information_gain_proxy | 41.12% | 39.21%-43.06% | 33.60% | 64.64% | 32.68% | 31.56% | 0.29 |

## Strategy Comparison Model

The primary model was a game-level logistic regression: `village_win ~ strategy + seed`, with `random` and seed 42 as references. Pairwise tests below use Holm correction across the requested comparisons.

| contrast | odds ratio | 95% CI | p | Holm p | interpretation |
|---|---:|---:|---:|---:|---|
| alternate_sides vs random | 1.161 | 1.038-1.299 | 0.009207 | 0.05524 | weak/inconclusive |
| alternate_sides vs right_to_left | 1.011 | 0.905-1.131 | 0.8419 | 1 | weak/inconclusive |
| alternate_sides vs inner_first | 1.089 | 0.973-1.218 | 0.1376 | 0.4127 | weak/inconclusive |
| alternate_sides vs edge_first | 1.118 | 0.999-1.250 | 0.05195 | 0.2078 | weak/inconclusive |
| right_to_left vs random | 1.148 | 1.026-1.284 | 0.01617 | 0.08084 | weak/inconclusive |
| information_gain_proxy vs random | 1.025 | 0.916-1.148 | 0.666 | 1 | weak/inconclusive |
| highest_p_wolf vs random | 0.786 | 0.701-0.882 | 3.921e-05 | 0.0002759 | statistically supported |
| highest_suspicion vs random | 0.785 | 0.700-0.880 | 3.449e-05 | 0.0002759 | statistically supported |

## Early Discovery and Mechanisms

Structured strategies did not consistently improve first-check wolf discovery relative to random. The stronger village outcomes for `alternate_sides` and `right_to_left` are therefore not fully explained by a first-check advantage. Discovery by check 2 or check 3 is somewhat better for some structured strategies, but the effect sizes are modest.

Staged models show that adding early discovery and seer survival changes some strategy coefficients, but because these variables occur after strategy assignment they should be interpreted as mechanism diagnostics rather than causal mediation estimates.

## Exploitation vs Diversification

Behavioral exploitation strategies had a combined village win rate of 35.52%, while the structured diversification group had 42.66%. The behavioral group also had lower seer survival. This supports the interpretation that aggressive behavioral targeting can narrow search without increasing useful information.

## Direction Asymmetry

`right_to_left` beat `random` descriptively, but the requested pairwise model did not survive Holm correction (OR=1.148, raw p=0.01617, Holm p=0.08084). The direct `alternate_sides` vs `right_to_left` contrast was inconclusive (OR=1.011, Holm p=1). Direction-asymmetry interaction tests are reported separately in `direction_asymmetry_analysis.csv`; because left/right ordering could reflect seat indexing artifacts, this should be isolated in a follow-up experiment.

## Robustness

Seed-stratified and leave-one-seed-out summaries are saved in `robustness_analysis.csv`. The strongest caution is that only five seeds are available, so seed fixed effects and leave-one-seed-out checks are more reliable than cluster-robust standard errors with five clusters. Conclusions that depend on one strategy's exact rank should be treated cautiously.

## Answers to Required Questions

1. **Which strategies are statistically better than random?** No positive strategy-vs-random contrast is statistically significant after Holm correction. `alternate_sides` and `right_to_left` are practically meaningful but statistically uncertain improvements over random. `highest_p_wolf` and `highest_suspicion` are statistically worse than random.
2. **Is `alternate_sides` truly best?** It is descriptively highest, but not statistically distinguishable from `right_to_left` in the requested contrast.
3. **Is `right_to_left` robust?** It is stronger than random in descriptive results and the unadjusted primary contrast, but it does not survive Holm correction. The direction asymmetry should therefore be treated as potentially structural or artifact-prone until a follow-up isolates seat-order effects.
4. **Do structured strategies outperform behavioral suspicion strategies?** Yes, in this dataset structured diversification outperforms behavioral exploitation descriptively and aligns with the poor model results for `highest_p_wolf` and `highest_suspicion`.
5. **Does early wolf discovery explain performance?** Only partially. Early discovery improves village outcomes, but strategy differences are not simply first-check discovery differences.
6. **Does diversification matter independently?** Evidence is suggestive but not causal. Coverage/diversity metrics are post-treatment, and their independent role should be tested in a targeted design.
7. **Why do behavioral strategies perform poorly?** They do not improve early discovery enough to compensate for lower seer survival and narrower search behavior.
8. **Is there evidence of simulation asymmetry?** Yes, the `left_to_right` vs `right_to_left` gap is large enough to merit a follow-up that randomizes or mirrors seat numbering.
9. **Next experiment:** isolate seat-order asymmetry by running mirrored seat labels or randomized clockwise/counter-clockwise orientation while holding role randomization and strategy logic constant.

## Output Files

- `descriptive_statistics.csv`
- `strategy_omnibus_tests.csv`
- `pairwise_strategy_contrasts.csv`
- `early_discovery_analysis.csv`
- `village_win_models.csv`
- `mechanism_models.csv`
- `exploitation_vs_diversification.csv`
- `direction_asymmetry_analysis.csv`
- `robustness_analysis.csv`
