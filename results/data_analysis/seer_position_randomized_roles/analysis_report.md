# Statistical Analysis: Seer Position with Randomized Roles

## Datasets Analyzed

- `results/ten_player_seer_position_randomized_roles_multi_seed_raw.csv`: seed-level raw results, 35 rows (7 strategies x 5 seeds).
- `results/ten_player_seer_position_randomized_roles_results.csv`: seed 42 single-seed reference results.

The original raw data files were preserved unchanged. All analysis outputs were written under `results/data_analysis/seer_position_randomized_roles/`.

## Methods

- Descriptive statistics across seeds: mean, sample standard deviation, minimum, maximum.
- 95% confidence intervals across seeds using the t critical value for n=5 seeds.
- Friedman omnibus tests across strategies for wolf win rate and seer wolf-discovery rate, using a chi-square approximation.
- Paired exact sign-flip permutation tests across matched seeds for all pairwise strategy comparisons.
- Holm correction for multiple pairwise comparisons.
- Effect sizes reported as paired Cohen's dz.
- Practical meaningfulness threshold: absolute difference of at least 3 percentage points.
- Outlier and influence scan using within-condition z-scores and leave-one-seed-out mean shifts.

## Main Descriptive Results

| Strategy | Wolf mean % | Wolf SD pp | 95% CI | Village mean % | Seer found wolf % | First check wolf % | Edge check % | Avg wolves on edge |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| default | 62.52 | 1.24 | [60.98, 64.06] | 37.48 | 32.10 | 33.44 | 41.63 | 1.20 |
| random | 59.48 | 2.04 | [56.94, 62.02] | 40.52 | 35.48 | 34.72 | 41.83 | 1.20 |
| edge_first | 58.56 | 2.51 | [55.44, 61.68] | 41.44 | 36.84 | 34.20 | 88.90 | 1.22 |
| inner_first | 58.32 | 2.76 | [54.89, 61.75] | 41.68 | 35.02 | 31.80 | 3.59 | 1.22 |
| highest_p_wolf | 65.12 | 1.99 | [62.65, 67.59] | 34.88 | 34.63 | 32.44 | 41.92 | 1.21 |
| highest_suspicion | 65.16 | 0.92 | [64.02, 66.30] | 34.84 | 35.21 | 33.56 | 42.36 | 1.22 |
| opposite_side | 60.48 | 1.90 | [58.13, 62.83] | 39.52 | 35.94 | 32.00 | 40.01 | 1.20 |

## Omnibus Strategy Tests

| Metric | Friedman Q | df | p-value | Interpretation |
|---|---:|---:|---:|---|
| wolf_win_rate | 24.04 | 6 | 0.0005 | strategy differences detected |
| seer_found_wolf_rate | 17.31 | 6 | 0.0082 | strategy differences detected |

## Edge-Priority Evaluation

`seer_edge_first` has a wolf win-rate mean of 58.56%, compared with 62.52% for default, 59.48% for random, and 58.32% for inner-first.

- edge_first vs default: mean wolf-rate difference -3.96 pp (negative favors edge_first), 95% CI [-8.02, 0.10], permutation p=0.0625, Holm p=1.0000, Cohen's dz=-1.21. This is practically meaningful but statistically inconclusive.
- edge_first vs random: mean wolf-rate difference -0.92 pp (negative favors edge_first), 95% CI [-3.95, 2.11], permutation p=0.5000, Holm p=1.0000, Cohen's dz=-0.38. This is inconclusive/small.
- edge_first vs inner_first: mean wolf-rate difference 0.24 pp (negative favors edge_first), 95% CI [-5.56, 6.04], permutation p=0.9375, Holm p=1.0000, Cohen's dz=0.05. This is inconclusive/small.

For wolf discovery, edge_first exceeds default by 4.73 pp (Holm p=1.0000).

Overall, the edge-priority advantage after role randomization is limited. It is directionally better than default and random for wolf win rate, but it is not statistically significant after multiple-comparison correction and it does not clearly outperform inner-first. The result is best treated as suggestive rather than confirmed.

## Strategy Comparison

The best village outcome by mean wolf win rate is `seer_inner_first` with wolf mean 58.32% and village mean 41.68%. The highest seer wolf-discovery rate is `seer_edge_first` at 36.84%. These are close enough that the analysis does not support a single dominant position-only strategy.

## Robustness and Outliers

No seed-strategy rows were flagged as outliers using the absolute z-score >= 2.0 threshold.
No seed was unusually influential across strategies using the absolute z-score >= 2.0 threshold.

The largest leave-one-seed-out wolf-rate mean shift is -1.07 pp for `seer_inner_first` seed 45. This indicates moderate seed sensitivity but no single run that fully drives the conclusion.

## Conclusions

- Statistically significant effects: The omnibus tests indicate that strategies differ overall, but pairwise Holm-corrected comparisons are conservative with only five seeds.
- Practically meaningful effects: edge_first reduces wolf win rate by about 3.96 pp relative to default, which is practically noticeable, but not statistically decisive after correction.
- Inconclusive effects: edge_first vs inner_first is essentially tied in wolf win rate, so there is no clear evidence that edge priority dominates inner priority after role randomization.
- Main finding: the apparent edge-priority advantage becomes weak and conditional once roles are randomized across seats.

Position should therefore be treated as a heuristic prior, not as standalone evidence. The randomized-role baseline makes this much harder to overinterpret, which is exactly the point of the test.

## Generated Files

- `statistical_summary.csv` and `.md`
- `pairwise_strategy_comparisons.csv` and `.md`
- `omnibus_strategy_tests.csv` and `.md`
- `outlier_influence.csv` and `.md`
- `seed_level_robustness.csv` and `.md`
- `wolf_win_rate_ci_by_strategy.svg`
- `seer_found_wolf_rate_ci_by_strategy.svg`
- `seed_level_wolf_win_rates.svg`
- `edge_priority_comparison.svg`
