# ML Stage 1.5 Schema

Datasets contain one row per legal candidate action sampled from a full-state pre-decision snapshot. Full rollout columns are labels/outcomes and are not legal observation features.

## Dataset Files

- `results/ml_optimization_stage15/ml_full_rollout_seer_dataset.csv`
- `results/ml_optimization_stage15/ml_full_rollout_wolf_kill_dataset.csv`
- `results/ml_optimization_stage15/ml_full_rollout_vote_dataset.csv`
- `results/ml_optimization_stage15/ml_surrogate_full_comparison.csv`
- `results/ml_optimization_stage15/ml_full_rollout_detail_rows.csv`
- `results/ml_optimization_stage15/ml_shadow_policy_decisions.csv`
- `results/ml_optimization_stage15/ml_split_assignments.csv`
- `results/ml_optimization_stage15/ml_behavioral_regime_registry.csv`
- `results/ml_optimization_stage15/ml_full_rollout_validation_summary.csv`
- `results/ml_optimization_stage15/ml_surrogate_validity_metrics.csv`
- `results/ml_optimization_stage15/ml_identity_generalization_metrics.csv`
- `results/ml_optimization_stage15/ml_action_value_generalization_metrics.csv`
- `results/ml_optimization_stage15/ml_cross_seed_metrics.csv`
- `results/ml_optimization_stage15/ml_cross_regime_metrics.csv`
- `results/ml_optimization_stage15/ml_feature_ablation_metrics.csv`
- `results/ml_optimization_stage15/ml_overfitting_diagnostics.csv`
- `results/ml_optimization_stage15/ml_shadow_policy_comparison.csv`
- `results/ml_optimization_stage15/ml_bootstrap_confidence_intervals.csv`
- `results/ml_optimization_stage15/ml_policy_regret_full_rollout.csv`

`ml_full_rollout_detail_rows.csv` contains one row per full simulator continuation and includes the `continuation_policy_id` used for that rollout.

## Splits

- train: seeds 42-49 for in-distribution regimes.
- validation: seeds 50-51 for in-distribution regimes.
- final_test: seeds 52-56 for in-distribution regimes.
- ood_test: held-out behavioral regimes.

## Feature Columns

- `round_number`
- `phase_is_night`
- `phase_is_day`
- `decision_type_is_seer_check`
- `decision_type_is_wolf_kill`
- `decision_type_is_day_vote`
- `actor_team_is_wolf`
- `actor_team_is_village`
- `alive_count`
- `dead_count`
- `public_revealed_role_count`
- `public_information_entropy_proxy`
- `number_of_public_check_results`
- `number_of_previous_eliminations`
- `actor_suspicion_score`
- `actor_p_wolf`
- `actor_risk_conservative`
- `actor_risk_aggressive`
- `actor_previous_votes_made`
- `actor_previous_speeches_made`
- `actor_known_teammate_count`
- `candidate_alive`
- `candidate_checked_by_actor_status`
- `candidate_public_role_known`
- `candidate_suspicion_score`
- `candidate_p_wolf`
- `candidate_received_accusations`
- `candidate_made_accusations`
- `candidate_wrong_accusation_count`
- `candidate_vote_received_count`
- `candidate_vote_made_count`
- `candidate_vote_switch_count`
- `candidate_speech_count`
- `candidate_defense_count`
- `candidate_role_claim_count`
- `candidate_special_role_claim_count`
- `candidate_trust_from_actor`
- `candidate_conflict_with_actor`
- `candidate_support_from_actor`
- `candidate_public_influence_proxy`
- `candidate_physical_seat_numeric`
- `candidate_seat_is_edge`
- `candidate_side_is_left`
- `candidate_distance_from_actor`
- `candidate_search_coverage_bonus`
- `candidate_was_previously_targeted_by_actor`
- `candidate_known_wolf_to_actor`
- `candidate_known_village_to_actor`
- `candidate_current_vote_count`
- `current_vote_total`
- `candidate_uncertainty_proxy`
- `candidate_survival_proxy`
