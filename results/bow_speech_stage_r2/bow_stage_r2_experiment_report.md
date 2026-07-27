# R2 Formal Bag-of-Words Speech Quantification Report

## Technical Summary

R2 implemented a real English text-based BoW shadow pipeline over 1600 source games and 32721 generated utterances. The final train-derived vocabulary contains 289 terms across 48 template families and 6 behavioral regimes. The pipeline does not alter live gameplay decisions.

The strongest scientific claim is implementation validity: tokenization, vocabulary construction, transparent scores, split isolation, and leakage checks are now present. Predictive results should be interpreted as controlled template-language evidence, not human-language generalization.

## Score Construct Validation

| Contrast | Score | Mean Diff | Cohen d | Grouped Bootstrap CI | Holm p |
| --- | --- | --- | --- | --- | --- |
| accusation_vs_neutral_werewolf_score | bow_werewolf_leaning_score | 0.043 | 2.519 | [0.042, 0.044] | 0.0000 |
| emotional_vs_neutral_intensity | bow_emotional_intensity_score | 0.029 | 0.787 | [0.026, 0.032] | 0.0000 |
| informative_vs_low_information_density | bow_information_density_score | 0.110 | 1.534 | [0.104, 0.116] | 0.0000 |
| deceptive_vs_non_deceptive_werewolf_score | bow_werewolf_leaning_score | 0.041 | 1.909 | [0.039, 0.043] | 0.0000 |

## Role-Prediction Model Comparison

| Model | Split | ROC-AUC | PR-AUC | Brier |
| --- | --- | --- | --- | --- |
| p_wolf_only | final_test | 0.569 | 0.372 | 0.209 |
| p_wolf_only | ood_template | 0.588 | 0.397 | 0.208 |
| p_wolf_only | ood_regime | 0.518 | 0.330 | 0.214 |
| suspicion_only | final_test | 0.515 | 0.373 | 0.211 |
| suspicion_only | ood_template | 0.519 | 0.389 | 0.211 |
| suspicion_only | ood_regime | 0.525 | 0.396 | 0.211 |
| bow_scores_only | final_test | 0.692 | 0.436 | 0.201 |
| bow_scores_only | ood_template | 0.614 | 0.358 | 0.216 |
| bow_scores_only | ood_regime | 0.643 | 0.390 | 0.207 |
| structured_speech_labels_only | final_test | 0.877 | 0.804 | 0.108 |
| structured_speech_labels_only | ood_template | 0.875 | 0.808 | 0.109 |
| structured_speech_labels_only | ood_regime | 0.917 | 0.909 | 0.076 |
| structured_labels_plus_bow_scores | final_test | 0.877 | 0.804 | 0.108 |
| structured_labels_plus_bow_scores | ood_template | 0.875 | 0.808 | 0.109 |
| structured_labels_plus_bow_scores | ood_regime | 0.917 | 0.908 | 0.075 |
| full_legal_combined | final_test | 0.890 | 0.823 | 0.106 |
| full_legal_combined | ood_template | 0.892 | 0.833 | 0.108 |
| full_legal_combined | ood_regime | 0.893 | 0.885 | 0.075 |
| full_bow_vector_naive_bayes | final_test | 0.758 | 0.728 | 0.152 |
| full_bow_vector_naive_bayes | ood_template | 0.361 | 0.248 | 0.692 |
| full_bow_vector_naive_bayes | ood_regime | 0.926 | 0.891 | 0.109 |

## Intent Classification

Multinomial Naive Bayes final-test macro F1: 1.000. OOD-template macro F1: 0.000.

## Leakage and Overfitting

The R2 leakage audit passes if all `hidden_information_leakage_flag` values are false, numeric IDs are normalized, and train-only vocabulary construction is used. See `bow_stage_r2_information_leakage_audit.md` and `bow_stage_r2_overfitting_audit.md`.

## R3 Readiness

Conclusion label: `promising but uncertain`. R2 validates the BoW pipeline and shows usable construct signal, but live decision integration remains intentionally deferred to R3.
