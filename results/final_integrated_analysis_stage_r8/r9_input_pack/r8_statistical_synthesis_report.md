# R8 Statistical Synthesis Report

This table consolidates final evidence while preserving stage-specific independent units.

| Hypothesis | Mechanism | Direction | Effect | Holm/Adjusted p | Conclusion |
| --- | --- | --- | --- | --- | --- |
| H_R8_01 | BoW speech quantification | positive predictive value | bow_scores_only AUC 0.6918; full_bow_vector AUC 0.7576 | not_reported | promising_but_uncertain |
| H_R8_02 | BoW live voting | harmful | -8.90909090909091 pp | 3.827255728455917e-09 | statistically_supported_harm |
| H_R8_03 | structured plus BoW live voting | harmful | -13.212121212121215 pp | 2.0024237615219272e-20 | statistically_supported_harm |
| H_R8_04 | Villager voting | improvement | 0.2445375 | 0.004995004995004995 | statistically_supported_improvement |
| H_R8_05 | Hunter policy | harmful | -0.1448 | 0.004995004995004995 | statistically_supported_harm |
| H_R8_06 | Seer reveal | positive payoff with exposure tradeoff | 0.07625 | 1.0 | promising_but_uncertain |
| H_R8_07 | Witch joint policy | positive payoff with waste tradeoff | 0.13119999999999998 | 0.056943056943056944 | promising_but_uncertain |
| H_R8_08 | Witch conservative policy | harmful | -0.3256 | 0.004995004995004995 | statistically_supported_harm |
| H_R8_09 | Werewolf deception/aggression | harmful | -0.61385 | 0.004995004995004995 | statistically_supported_harm |
| H_R8_10 | risk-adjusted payoff | differentiates roles | Werewolf highest mean 1.2095 and highest Sharpe-like 0.8434; Hunter worst CVaR95-like 2.2675 | not_applicable | statistically_supported_improvement |
| H_R8_11 | ML wolf-kill policy | harmful | -0.115 | 0.003265614619422763 | statistically_supported_harm |
| H_R8_12 | continuous ML control | harmful_direction_not_Holm_significant | -0.1 | 0.11450662203495152 | promising_but_uncertain |
| H_R8_13 | seat-position folklore | unsupported | edge_first first-check wolf 34.20% vs random 34.72%; adjusted village model OR 1.05 | not_significant_after_correction | no_supported_improvement |
| H_R8_14 | engine symmetry | validation_passed | 100% match rate; 0 divergences | not_applicable | diagnostic_only |
