# R8 Speech, BoW, and ML Report

Offline predictive value is reported separately from matched live policy value.

| Stage | Artifact/Policy | Type | Metric | Value | Conclusion |
| --- | --- | --- | --- | --- | --- |
| R2 | bow_scores_only | offline prediction | final-test ROC-AUC | 0.6918 | speech tokens contain wolf-role signal in generated utterances |
| R2 | full_bow_vector_naive_bayes | offline prediction | final-test ROC-AUC | 0.7576 | high-capacity lexical counts are template-sensitive |
| R2 | p_wolf_suspicion_structured | offline prediction | final-test ROC-AUC | 0.8913 | structured beliefs explain most predictive value |
| R2 | bow_scores_only_ood | template generalization | OOD template ROC-AUC | 0.6139 | BoW signal is template-bound |
| R3 | guarded_bow_010_live | live policy | village win-rate change | -8.90909090909091 | guarded BoW live integration was harmful |
| R3 | structured_bow_guarded_live | live policy | village win-rate change | -13.212121212121215 | adding BoW to structured live voting was harmful |
| R3 | selective_bow_vote_override_live | live policy | village win-rate change | -0.7272727272727264 | selective override did not rescue BoW live value |
| R3 | pure_bow_diagnostic_live | diagnostic live policy | village win rate | 0.2964 | diagnostic result does not override matched primary contrasts |
| ML Stage 1 | rollout_value_diagnostics | offline rollout | mean existing policy regret | 0.2975 | offline regret is diagnostic only |
| ML Stage 1.5 | logistic_regression_grouped_split | offline prediction | ROC-AUC | 0.6679 | prediction does not imply live policy improvement |
| ML Stage 2A | existing_rule | live policy reference | wolf win rate | 0.6950 | use as comparator |
| ML Stage 2A | frozen_hybrid_50_50 | matched live policy | wolf win-rate change | -0.115 | hybrid ML should not replace existing wolf-kill rule |
| ML Stage 2B | ml_first_kill_only | matched live intervention | wolf win-rate change | 0.01 | first-kill-only ML evidence is inconclusive |
| ML Stage 2B | continuous_frozen_ml | matched live repeated control | wolf win-rate change | -0.1 | continuous ML is not recommended for final configuration |
| ML Stage 2B | selective_ml_override | matched live selective override | wolf win-rate change | -0.01 | selective override did not provide robust live value |
| ML Stage 2B | existing_rule | live reference | wolf win rate | 0.7100 | current rule remains preferred over tested ML replacements |
