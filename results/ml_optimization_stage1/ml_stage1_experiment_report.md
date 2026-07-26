# ML Optimization Stage 1 Experiment Report

## Overview

This stage adds observation-safe decision logging, candidate-action datasets, deterministic counterfactual rollout-value estimates, interpretable baseline models, offline policy comparison, and information-leakage tests. Learned policies are not deployed into the live simulator.

## Observable Feature Design

Features are reconstructed from events available before each decision. Public signals include p_wolf, suspicion_score, speech and vote histories, trust-memory summaries, role-claim counts, seat features, and current vote context. Seer-private check results are available only to the checking seer. Wolf teammate identity is available only to wolf actors.

## Prohibited Features

- `actor_team_win_label`
- `candidate_is_wolf_label`
- `eventual_winner_label`
- `final_survival_label`
- `future_deaths`
- `future_speech`
- `future_votes`
- `rollout_best_action`
- `rollout_team_win_rate`
- `true_candidate_role_label`

## Pilot Scale Actually Used

- `seeds`: `[42, 43, 44, 45, 46]`
- `games_per_seed`: `12`
- `generated_games`: `60`
- `max_candidates`: `6`
- `decision_limits`: `{'seer_check': 500, 'wolf_kill': 500, 'day_vote': 1000}`
- `rollout_counts`: `{'seer_check': 5, 'wolf_kill': 5, 'day_vote': 3}`
- `dataset_generation_runtime_seconds`: `0.7934751510620117`
- `python_version`: `3.14.3`
- `total_runtime_seconds`: `8.137521743774414`
- `model_training_runtime_seconds`: `7.089494943618774`
- `total_rollout_simulations`: `24599`

## Dataset Sizes

| decision_type | decision_states | candidate_rows |
|---|---:|---:|
| seer_check | 98 | 588 |
| wolf_kill | 192 | 979 |
| day_vote | 1000 | 5588 |

Total candidate rows: 7155

## Split Design

Group-aware splits use seed/game family: seeds 42, 43, and 44 train; seed 45 validation; seed 46 test. Candidate rows from the same decision and game remain in one split.

## Identity Prediction Results

| context | model | status | ROC-AUC | PR-AUC | Brier | Top-1 hit |
|---|---|---|---:|---:|---:|---:|
| seer_candidate_states | existing_p_wolf | baseline | 0.6006235827664399 | 0.5093956962976756 | 0.2226772445436508 | 0.3333333333333333 |
| seer_candidate_states | existing_suspicion_score | baseline | 0.6082766439909297 | 0.5270558396455437 | 0.3243803943452381 | 0.3333333333333333 |
| seer_candidate_states | logistic_regression_stdlib | trained | 0.5338718820861678 | 0.4122014610115032 | 0.22522074221807398 | 0.42857142857142855 |
| seer_candidate_states | random_forest_sklearn | skipped_sklearn_unavailable |  |  |  |  |
| seer_candidate_states | hist_gradient_boosting_sklearn | skipped_sklearn_unavailable |  |  |  |  |
| village_vote_candidate_states | existing_p_wolf | baseline | 0.5042261731273681 | 0.4689207464324228 | 0.24251475792978397 | 0.4 |
| village_vote_candidate_states | existing_suspicion_score | baseline | 0.510929758088021 | 0.47678719974856737 | 0.3513712475640432 | 0.4 |
| village_vote_candidate_states | logistic_regression_stdlib | trained | 0.9457883998834159 | 0.8997051557863642 | 0.1464201723132452 | 1.0 |
| village_vote_candidate_states | random_forest_sklearn | skipped_sklearn_unavailable |  |  |  |  |
| village_vote_candidate_states | hist_gradient_boosting_sklearn | skipped_sklearn_unavailable |  |  |  |  |
| wolf_kill_candidate_states | identity_task_not_meaningful | not_meaningful_no_label_variance |  |  |  |  |

Best held-out identity model by ROC-AUC: `logistic_regression_stdlib` in `village_vote_candidate_states` (ROC-AUC 0.9457883998834159).

## Action-Value Model Results

| decision_type | model | status | RMSE | MAE | rank_corr | policy_value | avg_regret |
|---|---|---|---:|---:|---:|---:|---:|
| seer_check | mean_value_baseline | baseline | 0.2492878140745731 | 0.20404123335157817 | 0.2 | 0.5809523809523809 | 0.3238095238095238 |
| seer_check | ridge_regression_stdlib | trained | 0.25230845205441793 | 0.21110313912762058 | -0.08299319727891157 | 0.5047619047619047 | 0.4 |
| seer_check | random_forest_regressor_sklearn | skipped_sklearn_unavailable |  |  |  |  |  |
| seer_check | hist_gradient_boosting_regressor_sklearn | skipped_sklearn_unavailable |  |  |  |  |  |
| wolf_kill | mean_value_baseline | baseline | 0.21440853538151558 | 0.17617433071978528 | 0.09487179487179487 | 0.635897435897436 | 0.2717948717948718 |
| wolf_kill | ridge_regression_stdlib | trained | 0.21532491249985478 | 0.17481309548299917 | -0.07875457875457874 | 0.6820512820512821 | 0.22564102564102567 |
| wolf_kill | random_forest_regressor_sklearn | skipped_sklearn_unavailable |  |  |  |  |  |
| wolf_kill | hist_gradient_boosting_regressor_sklearn | skipped_sklearn_unavailable |  |  |  |  |  |
| day_vote | mean_value_baseline | baseline | 0.31075902989103077 | 0.2685146600919077 | 0.24926108374384237 | 0.5747126436781609 | 0.33333333333333337 |
| day_vote | ridge_regression_stdlib | trained | 0.3014014172729865 | 0.25550993470887023 | 0.1940886699507389 | 0.6551724137931034 | 0.25287356321839083 |
| day_vote | random_forest_regressor_sklearn | skipped_sklearn_unavailable |  |  |  |  |  |
| day_vote | hist_gradient_boosting_regressor_sklearn | skipped_sklearn_unavailable |  |  |  |  |  |

Best action-value model by within-decision rank correlation: `mean_value_baseline` for `day_vote`.

## Offline Policy Comparison

| decision_type | policy | states | value | regret | existing agreement |
|---|---|---:|---:|---:|---:|
| seer_check | existing_rule | 21 | 0.5904761904761905 | 0.3142857142857143 | 1.0 |
| seer_check | highest_existing_p_wolf | 21 | 0.6285714285714286 | 0.2761904761904762 | 0.09523809523809523 |
| seer_check | highest_existing_suspicion | 21 | 0.6380952380952382 | 0.2666666666666667 | 0.047619047619047616 |
| seer_check | ml_highest_wolf_probability | 21 | 0.5333333333333334 | 0.37142857142857144 | 0.14285714285714285 |
| seer_check | ml_highest_action_value | 21 | 0.5047619047619047 | 0.4 | 0.14285714285714285 |
| seer_check | ml_action_value_plus_exploration_bonus | 21 | 0.5619047619047619 | 0.34285714285714286 | 0.42857142857142855 |
| seer_check | epsilon_greedy_0_10_offline_expected | 21 | 0.5104761904761905 | 0.39428571428571424 | 0.14285714285714285 |
| wolf_kill | existing_wolf_strategy | 39 | 0.7128205128205128 | 0.19487179487179487 | 1.0 |
| wolf_kill | highest_threat_proxy | 39 | 0.676923076923077 | 0.23076923076923078 | 0.2564102564102564 |
| wolf_kill | highest_predicted_special_role_proxy | 39 | 0.6871794871794872 | 0.2205128205128205 | 0.2564102564102564 |
| wolf_kill | ml_highest_wolf_team_action_value | 39 | 0.6820512820512821 | 0.22564102564102567 | 0.20512820512820512 |
| day_vote | existing_voting_rule | 29 | 0.6206896551724138 | 0.2873563218390805 | 1.0 |
| day_vote | highest_suspicion | 29 | 0.5977011494252873 | 0.3103448275862069 | 0.8275862068965517 |
| day_vote | highest_ml_wolf_probability_for_village | 20 | 0.7 | 0.2 | 0.05 |
| day_vote | ml_highest_action_value | 29 | 0.6551724137931034 | 0.25287356321839083 | 0.5172413793103449 |
| day_vote | wolf_team_ml_vote_value | 9 | 0.6666666666666666 | 0.2592592592592593 | 0.5555555555555556 |

## Most Predictive Features

| task | context | feature | importance | signed_weight |
|---|---|---|---:|---:|
| action_value | day_vote | `candidate_current_vote_count` | 0.033017706777082545 | 0.033017706777082545 |
| action_value | day_vote | `candidate_made_accusations` | 0.028207263151115214 | 0.028207263151115214 |
| action_value | day_vote | `actor_known_teammate_count` | 0.021829567444348216 | 0.021829567444348216 |
| action_value | day_vote | `candidate_conflict_with_actor` | 0.021533265017842966 | 0.021533265017842966 |
| action_value | day_vote | `actor_team_is_village` | 0.01958031320709041 | -0.01958031320709041 |
| action_value | day_vote | `candidate_known_wolf_to_actor` | 0.01907908493400678 | -0.01907908493400678 |
| action_value | day_vote | `actor_team_is_wolf` | 0.018593368133100426 | 0.018593368133100426 |
| action_value | day_vote | `candidate_was_previously_targeted_by_actor` | 0.017304039740798863 | 0.017304039740798863 |
| action_value | day_vote | `candidate_wrong_accusation_count` | 0.015265726109295883 | 0.015265726109295883 |
| action_value | day_vote | `alive_count` | 0.00794924742966248 | -0.00794924742966248 |
| action_value | day_vote | `candidate_received_accusations` | 0.007687416146907838 | -0.007687416146907838 |
| action_value | day_vote | `candidate_distance_from_actor` | 0.006827310495922065 | 0.006827310495922065 |

## Leakage Audit

All information-leakage checks passed. Full details are in `ml_information_leakage_audit.md`.

## Answers to Required Questions

1. Observable features are listed in `ml_feature_registry.md` by actor/action type.
2. No leakage tests failed.
3. Decision states: seer=98, wolf=192, vote=1000.
4. Candidate-action rows: 7155.
5. Rollout simulations executed: 24599.
6. ML identity performance is compared against p_wolf and suspicion_score in `ml_identity_model_metrics.csv`.
7. The best held-out identity model is noted above when ROC-AUC is defined.
8. Predictive features are listed in `ml_feature_importance.csv`.
9. Action ranking is evaluated by within-decision rank correlation and top-action agreement.
10. The easiest action type is the one with the highest rank correlation in `ml_action_value_model_metrics.csv`.
11. Rule-based regret is summarized in `ml_policy_regret_summary.csv`.
12. Offline ML policy values are compared in `ml_offline_policy_comparison.csv`.
13. The seer exploration bonus appears as `ml_action_value_plus_exploration_bonus`.
14. Wolf prediction and action value are separate outputs, enabling correlation checks in Stage 2.
15. Prediction accuracy and strategic value are treated as different objectives.
16. ML Stage 2 should integrate only audited policies into live A/B simulations.

## Limitations

- scikit-learn is not installed in the local environment; sklearn baselines are skipped explicitly.
- Rollout values use a deterministic surrogate evaluator, not full mid-game engine cloning.
- This stage validates infrastructure and offline ranking, not live ML outcome gains.
