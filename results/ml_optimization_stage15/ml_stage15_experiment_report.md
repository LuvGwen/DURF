# ML Stage 1.5 Full-State Rollout Validation Report

## Overview

Stage 1.5 validates whether observation-safe ML signals survive full simulator continuation, grouped splits, and behavioral regime shifts. Learned policies remain in shadow mode only.

## Scale

- `source_seeds`: `[42, 43, 44, 50, 52, 53]`
- `games_per_regime_seed`: `2`
- `behavioral_regimes`: `7`
- `continuation_policies`: `7`
- `rollouts_per_policy`: `1`
- `decision_limits`: `{'seer_check': 80, 'wolf_kill': 80, 'day_vote': 120}`
- `max_candidates`: `4`
- `source_game_families`: `84`
- `decision_states`: `244`
- `candidate_rows`: `976`
- `full_rollout_simulations`: `6832`
- `bootstrap_resamples`: `500`
- `runtime_seconds`: `10.799897909164429`

## Dataset Sizes

| decision_type | states | candidate_rows |
|---|---:|---:|
| seer_check | 80 | 320 |
| wolf_kill | 80 | 320 |
| day_vote | 84 | 336 |

## Surrogate vs Full Rollout

| decision_type | Spearman | top-action agreement | MAE | validity |
|---|---:|---:|---:|---|
| seer_check | 0.2989434711276478 | 0.3875 | 0.38452380952380955 | partial validity |
| wolf_kill | 0.071781706852606 | 0.3125 | 0.27514880952380955 | weak validity |
| day_vote | 0.24187013217085407 | 0.35714285714285715 | 0.3242630385487528 | weak validity |

## Identity Generalization

| context | model | split | ROC-AUC | PR-AUC | Brier |
|---|---|---|---:|---:|---:|
| seer_candidate_states | existing_p_wolf | train | 0.5 | 1.0 | 0.24999999999999997 |
| seer_candidate_states | existing_suspicion | train | 0.5 | 1.0 | 0.4 |
| seer_candidate_states | logistic_regression_stdlib | train | 0.6504629629629629 | 0.5991533906575038 | 0.22526007311781035 |
| seer_candidate_states | existing_p_wolf | validation | 0.5 | 1.0 | 0.21999999999999997 |
| seer_candidate_states | existing_suspicion | validation | 0.5 | 1.0 | 0.325 |
| seer_candidate_states | logistic_regression_stdlib | validation | 0.6381766381766382 | 0.43804179000033083 | 0.22387967021899477 |
| seer_candidate_states | existing_p_wolf | final_test | 0.5 | 1.0 | 0.21999999999999997 |
| seer_candidate_states | existing_suspicion | final_test | 0.5 | 1.0 | 0.325 |
| seer_candidate_states | logistic_regression_stdlib | final_test | 0.5986467236467237 | 0.43056133465757757 | 0.23238490069301831 |
| seer_candidate_states | existing_p_wolf | ood_test | 0.5 | 1.0 | 0.24499999999999997 |
| seer_candidate_states | existing_suspicion | ood_test | 0.5 | 1.0 | 0.3875 |
| seer_candidate_states | logistic_regression_stdlib | ood_test | 0.5681369321922317 | 0.5238116568552745 | 0.23762208526756906 |
| village_vote_candidate_states | existing_p_wolf | train | 0.5907407407407408 | 1.0 | 0.21675595238095238 |
| village_vote_candidate_states | existing_suspicion | train | 0.5666666666666667 | 1.0 | 0.33630952380952384 |
| village_vote_candidate_states | logistic_regression_stdlib | train | 0.6975308641975309 | 0.6477797655429807 | 0.20381626792810928 |
| village_vote_candidate_states | existing_p_wolf | validation | 0.6634615384615384 | 1.0 | 0.17527777777777775 |
| village_vote_candidate_states | existing_suspicion | validation | 0.65 | 1.0 | 0.24131944444444445 |
| village_vote_candidate_states | logistic_regression_stdlib | validation | 0.698076923076923 | 0.6058750820902523 | 0.1767204865325536 |
| village_vote_candidate_states | existing_p_wolf | final_test | 0.6586059743954481 | 1.0 | 0.20187499999999997 |
| village_vote_candidate_states | existing_suspicion | final_test | 0.5789473684210527 | 1.0 | 0.3158482142857143 |
| village_vote_candidate_states | logistic_regression_stdlib | final_test | 0.6678520625889047 | 0.6315486779302569 | 0.19106471470473613 |
| village_vote_candidate_states | existing_p_wolf | ood_test | 0.5935483870967742 | 1.0 | 0.23536184210526315 |
| village_vote_candidate_states | existing_suspicion | ood_test | 0.5645161290322581 | 1.0 | 0.3848684210526316 |
| village_vote_candidate_states | logistic_regression_stdlib | ood_test | 0.5860215053763441 | 0.5271863257482058 | 0.22219514529283546 |

## Action-Value Generalization

| decision_type | model | split | top-action accuracy | policy value | regret |
|---|---|---|---:|---:|---:|
| seer_check | mean_baseline | train | 0.43333333333333335 | 0.3571428571428571 | 0.1857142857142857 |
| seer_check | ridge_regression_stdlib | train | 0.36666666666666664 | 0.3904761904761905 | 0.15238095238095237 |
| seer_check | mean_baseline | validation | 0.6 | 0.3714285714285714 | 0.11428571428571428 |
| seer_check | ridge_regression_stdlib | validation | 0.5 | 0.34285714285714286 | 0.14285714285714285 |
| seer_check | mean_baseline | final_test | 0.4 | 0.3214285714285714 | 0.14285714285714285 |
| seer_check | ridge_regression_stdlib | final_test | 0.4 | 0.33571428571428574 | 0.12857142857142856 |
| seer_check | mean_baseline | ood_test | 0.45 | 0.35 | 0.17142857142857143 |
| seer_check | ridge_regression_stdlib | ood_test | 0.5 | 0.3857142857142857 | 0.13571428571428573 |
| wolf_kill | mean_baseline | train | 0.5 | 0.7238095238095238 | 0.09047619047619047 |
| wolf_kill | ridge_regression_stdlib | train | 0.4 | 0.7333333333333333 | 0.08095238095238094 |
| wolf_kill | mean_baseline | validation | 0.4 | 0.7 | 0.17142857142857143 |
| wolf_kill | ridge_regression_stdlib | validation | 0.1 | 0.7428571428571429 | 0.1285714285714286 |
| wolf_kill | mean_baseline | final_test | 0.5 | 0.7214285714285714 | 0.12857142857142856 |
| wolf_kill | ridge_regression_stdlib | final_test | 0.35 | 0.7428571428571429 | 0.10714285714285716 |
| wolf_kill | mean_baseline | ood_test | 0.2 | 0.6571428571428571 | 0.20714285714285716 |
| wolf_kill | ridge_regression_stdlib | ood_test | 0.25 | 0.6714285714285715 | 0.19285714285714287 |
| day_vote | mean_baseline | train | 0.3 | 0.37619047619047613 | 0.1857142857142857 |
| day_vote | ridge_regression_stdlib | train | 0.4 | 0.41904761904761906 | 0.14285714285714285 |
| day_vote | mean_baseline | validation | 0.4 | 0.3142857142857143 | 0.17142857142857143 |
| day_vote | ridge_regression_stdlib | validation | 0.3 | 0.42857142857142855 | 0.05714285714285714 |
| day_vote | mean_baseline | final_test | 0.55 | 0.42857142857142855 | 0.10714285714285714 |
| day_vote | ridge_regression_stdlib | final_test | 0.35 | 0.42857142857142855 | 0.10714285714285714 |
| day_vote | mean_baseline | ood_test | 0.375 | 0.36904761904761907 | 0.14285714285714285 |
| day_vote | ridge_regression_stdlib | ood_test | 0.20833333333333334 | 0.3988095238095238 | 0.1130952380952381 |

## Shadow Policy Results

| decision_type | policy | split | value | improvement | regret |
|---|---|---|---:|---:|---:|
| seer_check | ml_identity_probability | validation | 0.3714285714285714 | 0.05714285714285714 | 0.11428571428571428 |
| seer_check | ml_full_action_value | validation | 0.48571428571428565 | 0.17142857142857143 | 0.0 |
| seer_check | ml_action_value_plus_exploration_bonus | validation | 0.48571428571428565 | 0.17142857142857143 | 0.0 |
| wolf_kill | highest_threat_baseline | validation | 0.7 | 0.014285714285714296 | 0.17142857142857143 |
| wolf_kill | ml_action_value_recommendation | validation | 0.8714285714285713 | 0.18571428571428572 | 0.0 |
| day_vote | highest_suspicion | validation | 0.2857142857142857 | -0.08571428571428572 | 0.2 |
| day_vote | ml_identity_probability | validation | 0.2857142857142857 | -0.08571428571428572 | 0.2 |
| day_vote | ml_action_value_recommendation | validation | 0.48571428571428565 | 0.11428571428571428 | 0.0 |
| seer_check | ml_identity_probability | final_test | 0.3214285714285714 | 0.05714285714285714 | 0.14285714285714285 |
| seer_check | ml_full_action_value | final_test | 0.46428571428571425 | 0.2 | 0.0 |
| seer_check | ml_action_value_plus_exploration_bonus | final_test | 0.46428571428571425 | 0.2 | 0.0 |
| wolf_kill | highest_threat_baseline | final_test | 0.7142857142857142 | 0.01428571428571428 | 0.13571428571428573 |
| wolf_kill | ml_action_value_recommendation | final_test | 0.85 | 0.15 | 0.0 |
| day_vote | highest_suspicion | final_test | 0.43571428571428567 | 0.06428571428571428 | 0.1 |
| day_vote | ml_identity_probability | final_test | 0.43571428571428567 | 0.06428571428571428 | 0.1 |
| day_vote | ml_action_value_recommendation | final_test | 0.5357142857142857 | 0.16428571428571428 | 0.0 |
| seer_check | ml_identity_probability | ood_test | 0.35 | 0.03571428571428572 | 0.17142857142857143 |
| seer_check | ml_full_action_value | ood_test | 0.5214285714285715 | 0.20714285714285713 | 0.0 |
| seer_check | ml_action_value_plus_exploration_bonus | ood_test | 0.5214285714285715 | 0.20714285714285713 | 0.0 |
| wolf_kill | highest_threat_baseline | ood_test | 0.7428571428571429 | 0.02857142857142857 | 0.12142857142857144 |
| wolf_kill | ml_action_value_recommendation | ood_test | 0.8642857142857142 | 0.15 | 0.0 |
| day_vote | highest_suspicion | ood_test | 0.35714285714285715 | -0.03571428571428572 | 0.15476190476190477 |
| day_vote | ml_identity_probability | ood_test | 0.36904761904761907 | -0.023809523809523808 | 0.14285714285714285 |
| day_vote | ml_action_value_recommendation | ood_test | 0.5119047619047619 | 0.11904761904761905 | 0.0 |

## Final Questions

1. The simulator can be cloned and continued from sampled mid-game states; snapshot equivalence passed 10 / 10 checks.
2. Full-state rollout reproduces under fixed requests; this is covered by `test_ml_full_rollout.py` and deterministic rollout seeds derived from snapshot/action/policy IDs.
3. Surrogate approximation is action-specific: seer_check Spearman=0.299, wolf_kill Spearman=0.072, day_vote Spearman=0.242.
4. Strongest surrogate validity: seer_check (partial validity).
5. Weakest surrogate validity: wolf_kill (weak validity).
6. On final-test village vote states, logistic ROC-AUC=0.668, existing p_wolf ROC-AUC=0.659; identity gains are therefore modest under grouped evaluation.
7. The Stage 1 pilot ROC-AUC around 0.9458 does not survive this stricter grouped pilot: final-test logistic ROC-AUC is 0.668 for village votes and 0.599 for seer candidate states.
8. Train/validation/test gaps are listed in `ml_overfitting_diagnostics.csv`; 1 row(s) are flagged.
9. Evidence of overfitting exists for flagged rows, so all Stage 1.5 model decisions are classified as shadow-mode only.
10. Feature groups with the strongest final-test vote ROC-AUC in this pilot: existing_rule_scores=0.731, base_scores_only=0.731, no_spatial_features=0.683.
11. Feature groups near chance on final test include: speech_features, voting_history_features, accusation_defense_features, trust_relationship_features, spatial_position_features.
12-14. Final-test shadow value for `seer_check` ML action-value recommendation: value=0.464, improvement=0.200, regret=0.000.
12-14. Final-test shadow value for `wolf_kill` ML action-value recommendation: value=0.850, improvement=0.150, regret=0.000.
12-14. Final-test shadow value for `day_vote` ML action-value recommendation: value=0.536, improvement=0.164, regret=0.000.
15-16. Stability across continuation policies, seeds, and behavioral regimes is exported in policy-value variance, `ml_cross_seed_metrics.csv`, and `ml_cross_regime_metrics.csv`.
17. ML recommendations improve full-rollout value on some held-out shadow comparisons, but the pilot remains small and offline.
18. Frozen model selections are documented in `model_selection_manifest.json`; validation split only is used for selection.
19. Tree models are rejected because scikit-learn is unavailable; the flagged seer identity logistic result is treated as overfit.
20. The project is not ready for ML Stage 2 live A/B testing; it is ready for larger shadow-mode full-rollout validation.
