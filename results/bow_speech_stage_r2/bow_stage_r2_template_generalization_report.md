# R2 BoW Template Generalization Report

The unseen-template split holds template families out of training entirely. Large final-test to OOD-template drops are interpreted as template dependence rather than robust language understanding.

| Model | Final AUC | OOD Template AUC | OOD-Final Gap | Label |
| --- | --- | --- | --- | --- |
| base_rate | 0.500 | 0.500 | 0.000 | stable_or_uncertain |
| bow_scores_only | 0.692 | 0.614 | -0.078 | template_bound |
| full_bow_vector_naive_bayes | 0.758 | 0.361 | -0.396 | template_bound |
| full_legal_combined | 0.890 | 0.892 | 0.002 | stable_or_uncertain |
| p_wolf_only | 0.569 | 0.588 | 0.019 | stable_or_uncertain |
| p_wolf_plus_suspicion | 0.567 | 0.586 | 0.018 | stable_or_uncertain |
| p_wolf_suspicion_structured | 0.891 | 0.893 | 0.002 | stable_or_uncertain |
| structured_labels_plus_bow_scores | 0.877 | 0.875 | -0.002 | stable_or_uncertain |
| structured_speech_labels_only | 0.877 | 0.875 | -0.002 | stable_or_uncertain |
| suspicion_only | 0.515 | 0.519 | 0.004 | stable_or_uncertain |
