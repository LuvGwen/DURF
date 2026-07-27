# R2 Research Report: Formal Bag-of-Words Speech Quantification

## 1. Overview

This stage converts the simulator's structured speech acts into English natural-language utterances, tokenizes them deterministically, extracts transparent BoW scores, and evaluates whether those scores recover known intent and add predictive information beyond prior structured signals.

## 2. Data Scale and Splits

The R2 dataset contains 1600 source games and 32721 utterances. Splits are grouped by game family and template family. Vocabulary construction uses train rows only. OOD-template rows use template families withheld from training, and OOD-regime rows use behavioral regimes withheld from training.

## 3. Score Definitions

- Werewolf-leaning score: normalized weighted average of manipulation, deflection, pressure, accusation, and certainty terms.
- Emotional-intensity score: normalized intensity weights plus exclamation markers.
- Information-density score: information weights, type-token ratio, player-reference specificity, causal/evidence terms, and a vague-word penalty.

## 4. Main Predictive Results

Final-test ROC-AUC values: BoW scores only = 0.692, p_wolf only = 0.569, suspicion only = 0.515, structured labels only = 0.877, full legal combined = 0.890.

## 5. Generalization and Ablations

Unseen-template and unseen-regime results are exported in `bow_template_generalization_metrics.csv` and `bow_regime_generalization_metrics.csv`. Keyword ablations test whether role words, player placeholders, accusation verbs, emotional punctuation, and deception-specific terms drive results.

## 6. Scientific Interpretation

R2 establishes a genuine BoW pipeline and validates the three proposal-level speech constructs. BoW-only role prediction improves over existing p_wolf and suspicion baselines, but structured speech labels remain stronger and the full legal combined model does not clearly improve over p_wolf + suspicion + structured labels. The evidence is best classified as `promising but uncertain`: the system is useful as a shadow measurement layer, but live decision integration needs a separate R3 experiment with matched game-level outcomes.

## 7. Required Final Questions

1. Was a real text-based BoW pipeline implemented? Yes.
2. How many games and utterances were generated? 1600 games and 32721 utterances.
3. How many independent game families and template families were used? 1600 game families and 48 template families.
4. What is the final vocabulary size? 289.
5. What are the three score formulas? See `bow_score_definition_manifest.json`; they are normalized weighted sums for werewolf leaning, emotional intensity, and information density.
6. Does werewolf-leaning distinguish wolves from villagers? Yes descriptively in score/model form; BoW scores reached final-test ROC-AUC 0.692.
7. Does emotional intensity distinguish emotional speech types? Yes; the pre-specified emotional-vs-neutral contrast is significant after Holm correction.
8. Does information density distinguish informative speech? Yes; the informative-vs-low-information contrast is significant after Holm correction.
9. Does BoW outperform existing p_wolf? Yes for BoW scores alone on final test (0.692 vs 0.569 ROC-AUC).
10. Does BoW outperform existing suspicion? Yes for BoW scores alone on final test (0.692 vs 0.515 ROC-AUC).
11. Does BoW add value beyond structured speech labels? Not clearly; structured labels alone reached 0.877 and structured labels plus BoW scores reached 0.877.
12. Does structured + BoW outperform either alone? Structured + BoW scores outperform BoW scores alone but not structured labels alone; the full legal combined model reached 0.890.
13. Does performance survive unseen-template testing? Rule-based BoW scores retain signal, but the full BoW vector NB model drops from 0.758 to 0.361, so the vector model is template-bound.
14. Does performance survive unseen-regime testing? Most combined/structured models remain strong in OOD-regime rows, but this is a simulator-regime test rather than human-language transfer.
15. Does performance survive removal of direct role words? Yes for the BoW logistic ablation; final-test AUC change is 0.000.
16. Which vocabulary terms are most influential? See `bow_feature_importance.csv`.
17. Is the model overfitting to template wording? The full vector NB model shows strong OOD-template weakness; transparent scores are less template-sensitive.
18. Did any leakage checks fail? No; the leakage audit status is PASS.
19. Is pure BoW scientifically useful? Yes as a controlled measurement layer, but not sufficient as a standalone decision policy.
20. Is hybrid structured + BoW useful? Possibly for measurement, but no robust added value beyond existing structured + p_wolf/suspicion features is established in R2.
21. Is the BoW module ready for R3 live decision integration? It is ready for controlled R3 testing, not for unguarded replacement of existing decisions.
22. What exact R3 experiment should be run? A matched multi-seed live-game ablation comparing existing belief/voting updates against BoW-weighted belief/voting updates, with credibility and speaker-memory safeguards enabled.

## 8. Next Hypothesis

H-R3: Integrating validated BoW speech scores into belief and voting updates will improve village coordination only when credibility and speaker-memory weights prevent wolves from exploiting high-intensity accusation language.
