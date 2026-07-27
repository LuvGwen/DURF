# R2 BoW Overfitting Audit

Models with train-validation or train-final AUC gap above 0.05: 0.

| Model | Train AUC | Validation AUC | Final AUC | Train-Final Gap | Flag |
| --- | --- | --- | --- | --- | --- |
| base_rate | 0.500 | 0.500 | 0.500 | 0.000 | False |
| bow_scores_only | 0.688 | 0.691 | 0.692 | -0.004 | False |
| full_bow_vector_naive_bayes | 0.766 | 0.763 | 0.758 | 0.008 | False |
| full_legal_combined | 0.890 | 0.890 | 0.890 | 0.001 | False |
| p_wolf_only | 0.564 | 0.573 | 0.569 | -0.005 | False |
| p_wolf_plus_suspicion | 0.564 | 0.573 | 0.567 | -0.003 | False |
| p_wolf_suspicion_structured | 0.891 | 0.890 | 0.891 | -0.000 | False |
| structured_labels_plus_bow_scores | 0.875 | 0.878 | 0.877 | -0.002 | False |
| structured_speech_labels_only | 0.875 | 0.878 | 0.877 | -0.002 | False |
| suspicion_only | 0.517 | 0.528 | 0.515 | 0.002 | False |
