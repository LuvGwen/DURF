# ML Stage 2B Research Report

## Background

Stage 2A found that the existing rule achieved 69.50% wolf win rate, while
continuous frozen ML achieved 61.00% and the 50/50 hybrid achieved 58.00%.
Stage 2B therefore asks whether the failure came from repeated ML control,
distribution shift, low-margin rankings, hybrid score incompatibility, or
downstream simulator interactions.

## Data Analysis

The primary analysis uses matched complete-game contrasts and McNemar-style
paired binomial tests with Holm correction across four pre-specified
comparisons. Decision-level and candidate-level rows are used only for
mechanism diagnosis.

## Live Policy Results

| Policy | Games | Wolf Win | Village Win | Avg Rounds | Avg ML Interventions | Strong Shift Rate |
| --- | --- | --- | --- | --- | --- | --- |
| existing_rule | 200 | 71.00% | 29.00% | 3.4100 | 0.0000 | 57.25% |
| ml_first_kill_only | 200 | 72.00% | 28.00% | 3.4200 | 1.0000 | 57.11% |
| ml_single_random_kill | 200 | 66.50% | 33.50% | 3.3500 | 0.9700 | 55.01% |
| ml_first_two_kills | 200 | 63.00% | 37.00% | 3.3750 | 2.0000 | 54.53% |
| continuous_frozen_ml | 200 | 61.00% | 39.00% | 3.3450 | 3.3450 | 54.22% |
| existing_with_ml_shadow | 200 | 71.00% | 29.00% | 3.4100 | 0.0000 | 57.25% |
| selective_ml_override | 200 | 70.00% | 30.00% | 3.4200 | 0.1850 | 57.11% |
| high_confidence_shadow | 200 | 71.00% | 29.00% | 3.4100 | 0.0000 | 57.25% |

## Formal Inference

| Contrast | Matched Sets | Diff | CI Low | CI High | Discordant OR | Raw p | Holm p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ml_first_kill_only_vs_existing_rule | 200 | 1.00% | -2.67% | 4.67% | 1.3077 | 0.7905 | 1.0000 |
| ml_first_two_kills_vs_existing_rule | 200 | -8.00% | -15.66% | -0.34% | 0.5949 | 0.0559 | 0.1677 |
| continuous_frozen_ml_vs_existing_rule | 200 | -10.00% | -18.45% | -1.55% | 0.5876 | 0.0286 | 0.1145 |
| selective_ml_override_vs_existing_rule | 200 | -1.00% | -2.38% | 0.38% | 0.2000 | 0.5000 | 1.0000 |

## Distribution Shift

| Policy | Shift | Rows | Wolf Win | Avg Margin | Avg Cum. ML |
| --- | --- | --- | --- | --- | --- |
| continuous_frozen_ml | in_distribution | 152 | 61.84% | 0.0086 | 1.0000 |
| continuous_frozen_ml | mild_shift | 137 | 62.77% | 0.0108 | 1.7080 |
| continuous_frozen_ml | strong_shift | 380 | 58.68% | 0.0108 | 2.9395 |
| existing_rule | in_distribution | 177 | 73.45% | 0.0093 | 0.0000 |
| existing_rule | mild_shift | 99 | 66.67% | 0.0099 | 0.0000 |
| existing_rule | strong_shift | 406 | 69.70% | 0.0125 | 0.0000 |
| existing_with_ml_shadow | in_distribution | 177 | 73.45% | 0.0093 | 0.0000 |
| existing_with_ml_shadow | mild_shift | 99 | 66.67% | 0.0099 | 0.0000 |
| existing_with_ml_shadow | strong_shift | 406 | 69.70% | 0.0125 | 0.0000 |
| high_confidence_shadow | in_distribution | 177 | 73.45% | 0.0093 | 0.0000 |
| high_confidence_shadow | mild_shift | 99 | 66.67% | 0.0099 | 0.0000 |
| high_confidence_shadow | strong_shift | 406 | 69.70% | 0.0125 | 0.0000 |
| ml_first_kill_only | in_distribution | 152 | 75.66% | 0.0086 | 1.0000 |
| ml_first_kill_only | mild_shift | 127 | 68.50% | 0.0102 | 1.0000 |
| ml_first_kill_only | strong_shift | 405 | 71.60% | 0.0120 | 1.0000 |
| ml_first_two_kills | in_distribution | 152 | 67.11% | 0.0086 | 1.0000 |
| ml_first_two_kills | mild_shift | 137 | 59.12% | 0.0107 | 1.6496 |
| ml_first_two_kills | strong_shift | 386 | 61.66% | 0.0113 | 2.0000 |
| ml_single_random_kill | in_distribution | 169 | 68.64% | 0.0091 | 0.3314 |
| ml_single_random_kill | mild_shift | 114 | 65.79% | 0.0106 | 0.7193 |

## Downstream Mechanisms

| Policy | Decisions | Special Role | Seer | Witch | Hunter | Witch Save | Hunter Retaliation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| continuous_frozen_ml | 669 | 40.51% | 10.46% | 14.05% | 15.99% | 26.61% | 17.79% |
| existing_rule | 682 | 92.82% | 49.71% | 25.22% | 17.89% | 25.81% | 20.67% |
| existing_with_ml_shadow | 682 | 92.82% | 49.71% | 25.22% | 17.89% | 25.81% | 20.67% |
| high_confidence_shadow | 682 | 92.82% | 49.71% | 25.22% | 17.89% | 25.81% | 20.67% |
| ml_first_kill_only | 684 | 75.88% | 32.46% | 23.83% | 19.59% | 26.46% | 18.86% |
| ml_first_two_kills | 675 | 59.85% | 25.48% | 17.19% | 17.19% | 26.37% | 17.63% |
| ml_single_random_kill | 670 | 77.91% | 42.84% | 19.10% | 15.97% | 26.57% | 17.61% |
| selective_ml_override | 684 | 89.18% | 45.32% | 25.29% | 18.57% | 25.58% | 20.32% |

## Hybrid Failure

| Policy | Decisions | ML/Rule Disagree | Hybrid=ML | Hybrid=Rule | Hybrid=Neither | Diagnosis |
| --- | --- | --- | --- | --- | --- | --- |
| continuous_frozen_ml | 669 | 82.21% | 46.04% | 62.63% | 9.12% | multiple mechanisms |
| existing_rule | 682 | 85.19% | 44.43% | 62.76% | 7.62% | multiple mechanisms |
| existing_with_ml_shadow | 682 | 85.19% | 44.43% | 62.76% | 7.62% | multiple mechanisms |
| high_confidence_shadow | 682 | 85.19% | 44.43% | 62.76% | 7.62% | multiple mechanisms |
| ml_first_kill_only | 684 | 85.09% | 43.86% | 62.87% | 8.19% | multiple mechanisms |
| ml_first_two_kills | 675 | 81.33% | 45.93% | 63.26% | 9.48% | multiple mechanisms |
| ml_single_random_kill | 670 | 85.07% | 44.48% | 62.69% | 7.76% | multiple mechanisms |
| selective_ml_override | 684 | 85.67% | 45.03% | 61.55% | 7.75% | multiple mechanisms |

## Answers to Stage 2B Questions

1. One ML intervention is assessed by `ml_first_kill_only` and single-action rollouts.
2. Two-step intervention is assessed by `ml_first_two_kills`.
3. Continuous ML is assessed by `continuous_frozen_ml`.
4. Repeated shift is assessed by cumulative intervention and shift summaries.
5. Prediction reliability is proxied by margins, novelty, and shift categories.
6. Low-margin decisions are summarized in `stage2b_margin_band_analysis.csv`.
7. OOD states are summarized in `stage2b_distribution_shift_summary.csv`.
8. Selective subgroup evidence is in `stage2b_selective_override_analysis.csv`.
9. Selective override is diagnostic only unless final-test results are stable.
10. Override coverage is reported in the selective override table.
11. Seed stability is in `stage2b_seed_robustness.csv`.
12. Regime stability is in `stage2b_regime_robustness.csv`.
13. Hybrid diagnostics point to score/rank incompatibility when hybrid differs from both source systems or dilutes special-role targeting.
14. Witch-save risk is in downstream summaries.
15. Hunter-retaliation risk is in downstream summaries.
16. Special-role targeting is in downstream summaries.
17. Vote-control proxy is in downstream summaries.
18. The offline-to-live gap is treated as a mixed mechanism unless a single diagnostic dominates.
19. The frozen ML model is retained for diagnostic research only.
20. The existing rule remains the default.
21. Broad ML wolf-kill optimization should not continue without stronger selective evidence.
22. The exact next proposal-completion stage is R2: Formal Bag-of-Words Speech Quantification.

## Conclusion

Conclusion label: `weak/inconclusive`.
