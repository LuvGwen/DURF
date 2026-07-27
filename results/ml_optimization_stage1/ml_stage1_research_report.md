# ML Stage 1 Research Report: Observation-Safe Logging And Offline ML Pilot

## 1. Background

ML Stage 1 was the first machine-learning optimization stage for the DURF Werewolf simulation. Its goal was to determine whether game states could be logged in an observation-safe way and converted into candidate-action datasets for identity prediction and action-value modeling.

## 2. Prior-Stage Connection

Stages 1-4 had already implemented the game engine, role actions, speech-like signals, belief updates, herding, wolf deception, credibility costs, speaker memory, and ten-player variants. ML Stage 1 treated these mechanisms as a source of simulated decisions and public state features.

## 3. Hypothesis

Observation-safe features should contain learnable signals about hidden wolf identity and action value without using prohibited hidden labels as model inputs.

## 4. Pre-Specified Outcomes

Primary outcomes were identity prediction metrics, action-value ranking metrics, offline policy value, regret, and leakage-audit status.

## 5. Experimental Design

The stage generated candidate rows for seer checks, wolf night kills, and day votes. Learned policies were not deployed into the live simulator. Splits were grouped by seed/game family where possible: seeds 42-44 for training, 45 for validation, and 46 for testing.

## 6. Data Scale

The pilot used seeds 42-46, 12 games per seed, 60 generated games, and 24,599 rollout simulations. Dataset sizes were 98 seer-check states with 588 candidate rows, 192 wolf-kill states with 979 rows, and 1,000 day-vote states with 5,588 rows, for 7,155 total candidate rows.

## 7. Independent Sample Definition

The independent unit is closer to a source game family or decision state than a candidate row. Candidate rows from the same decision are not independent.

## 8. Implementation

Feature logging used only information available before each decision. Public features included `p_wolf`, `suspicion_score`, speech and vote histories, trust summaries, role claims, seat features, and vote context. Seer-private information was available only to the seer, and wolf teammate identity was available only to wolf actors.

## 9. Validation

The leakage audit listed prohibited fields such as `candidate_is_wolf_label`, `true_candidate_role_label`, `eventual_winner_label`, future deaths, future speech, and rollout labels. The Stage 1 report states that all leakage checks passed.

## 10. Data Analysis

The analysis was primarily descriptive and pilot-level. It reported ROC-AUC, PR-AUC, Brier score, log loss, top-k identity metrics, RMSE, MAE, rank correlation, policy value, regret, and offline agreement with existing rules.

## 11. Descriptive Findings

The most striking pilot identity result was the village-vote logistic model ROC-AUC of 0.9458, compared with existing `p_wolf` ROC-AUC of 0.5042 and existing suspicion ROC-AUC of 0.5109 in that pilot split. The best wolf-kill ridge action-value policy had value 0.6821, below the existing wolf strategy value of 0.7128 in the offline comparison.

## 12. Formal Inference

Formal statistical inference was not performed in Stage 1. No confidence intervals or adjusted p-values were reported for model-performance differences. Stage 1 should therefore be read as an implementation and feasibility pilot, not a final model-validation result.

## 13. Robustness

Robustness was limited. The split used five seeds, but the later ML Stage 1.5 grouped/full-rollout evaluation superseded Stage 1 for generalization claims.

## 14. Leakage, Overfitting, And Design Audit

Leakage checks passed, but later evidence showed that row-level or small grouped pilots could still be optimistic. The Stage 1 village-vote ROC-AUC of about 0.9458 did not survive stricter grouped evaluation.

## 15. Scientific Interpretation

ML Stage 1 successfully built the data infrastructure but did not prove that learned policies improve live game outcomes. The correct scientific interpretation is that observation-safe logging is feasible and that some identity signals appear learnable, but the strength of those signals required stricter validation.

## 16. Conclusion Label

Conclusion label: `weak/inconclusive` for predictive or policy-improvement claims; `implementation validated` for observation-safe logging and leakage-audit infrastructure.

## 17. Limitations

The stage used a small pilot sample, candidate-row outputs, surrogate rollout values, and no live policy deployment. scikit-learn baselines were skipped because scikit-learn was unavailable.

## 18. Next Hypothesis

The next hypothesis was that grouped full-state rollout validation would separate true generalization from row-split optimism and surrogate artifacts.

## 19. Source Files

- `ml_decision_logging.py`
- `ml_dataset_builder.py`
- `ml_model_training.py`
- `results/ml_optimization_stage1/ml_stage1_experiment_report.md`
- `results/ml_optimization_stage1/ml_identity_model_metrics.csv`
- `results/ml_optimization_stage1/ml_action_value_model_metrics.csv`
- `results/ml_optimization_stage1/ml_offline_policy_comparison.csv`
- `results/ml_optimization_stage1/ml_information_leakage_audit.md`

## 20. Reproducibility Information

The Stage 1 report records the seed list, generated-game count, decision limits, rollout counts, Python version, and runtime. Source artifacts are committed in the repository.

## 21. Commit Information

This reconstruction used repository state `e4e583387febd51dddc6330076db6f2a2a7532bc`. The current documentation commit is recorded after this stage is committed.
