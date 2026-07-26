# ML Stage 1 Feature Registry

This registry defines observation-safe feature columns for the first machine-learning optimization stage. True hidden roles, future outcomes, and final winner fields are labels only and must not be used as model features.

## Prohibited Inputs

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

## Feature Definitions

| name | type | actors | earliest_phase | visibility | source | missing |
|---|---|---|---|---|---|---|
| `round_number` | integer | all | night | public | `build_actor_observation` | 0 |
| `phase_is_night` | integer | seer,wolf_team | night | public | `build_actor_observation` | 0 |
| `phase_is_day` | integer | all | day | public | `build_actor_observation` | 0 |
| `decision_type_is_seer_check` | integer | seer | night | public | `build_candidate_feature_row` | 0 |
| `decision_type_is_wolf_kill` | integer | wolf_team | night | team-private | `build_candidate_feature_row` | 0 |
| `decision_type_is_day_vote` | integer | all | day | public | `build_candidate_feature_row` | 0 |
| `actor_team_is_wolf` | integer | self | night | role-private | `build_actor_observation` | 0 |
| `actor_team_is_village` | integer | self | night | role-private | `build_actor_observation` | 0 |
| `alive_count` | integer | all | night | public | `build_actor_observation` | 0 |
| `dead_count` | integer | all | night | public | `build_actor_observation` | 0 |
| `public_revealed_role_count` | integer | all | day | public | `build_actor_observation` | 0 |
| `public_information_entropy_proxy` | float | all | night | public | `compute_score_state` | 0.5 |
| `number_of_public_check_results` | integer | all | night | public | `build_actor_observation` | 0 |
| `number_of_previous_eliminations` | integer | all | day | public | `build_actor_observation` | 0 |
| `actor_suspicion_score` | float | all | night | public | `compute_score_state` | 0.0 |
| `actor_p_wolf` | float | all | night | public | `compute_score_state` | initial_p_wolf |
| `actor_risk_conservative` | integer | all | night | role-private | `build_actor_observation` | 0 |
| `actor_risk_aggressive` | integer | all | night | role-private | `build_actor_observation` | 0 |
| `actor_previous_votes_made` | integer | all | day | public | `event_history_counts` | 0 |
| `actor_previous_speeches_made` | integer | all | day | public | `event_history_counts` | 0 |
| `actor_known_teammate_count` | integer | wolf_team | night | team-private | `build_actor_observation` | 0 |
| `candidate_alive` | integer | all | night | public | `build_candidate_feature_row` | 0 |
| `candidate_checked_by_actor_status` | integer | seer | night | role-private | `seer_private_check_memory` | 0 |
| `candidate_public_role_known` | integer | all | day | public | `revealed_role_memory` | 0 |
| `candidate_suspicion_score` | float | all | night | public | `compute_score_state` | 0.0 |
| `candidate_p_wolf` | float | all | night | public | `compute_score_state` | initial_p_wolf |
| `candidate_received_accusations` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_made_accusations` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_wrong_accusation_count` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_vote_received_count` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_vote_made_count` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_vote_switch_count` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_speech_count` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_defense_count` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_role_claim_count` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_special_role_claim_count` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_trust_from_actor` | float | all | day | role-private | `speaker_trust_from_past_events` | 0.5 |
| `candidate_conflict_with_actor` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_support_from_actor` | integer | all | day | public | `event_history_counts` | 0 |
| `candidate_public_influence_proxy` | float | all | day | public | `event_history_counts` | 0.0 |
| `candidate_physical_seat_numeric` | integer | all | night | public | `position_model` | displayed seat if physical seat unavailable |
| `candidate_seat_is_edge` | integer | all | night | public | `position_model` | 0 |
| `candidate_side_is_left` | integer | all | night | public | `position_model` | 0 |
| `candidate_distance_from_actor` | integer | all | night | public | `position_model` | 0 |
| `candidate_search_coverage_bonus` | float | seer | night | role-private | `seer_private_check_memory` | 0.0 |
| `candidate_was_previously_targeted_by_actor` | integer | all | day | public/role-private | `event_history_counts` | 0 |
| `candidate_known_wolf_to_actor` | integer | seer,wolf_team | night | role-private/team-private | `known_information_for_actor` | 0 |
| `candidate_known_village_to_actor` | integer | seer | night | role-private | `known_information_for_actor` | 0 |
| `candidate_current_vote_count` | integer | all | day | public | `current_vote_state` | 0 |
| `current_vote_total` | integer | all | day | public | `current_vote_state` | 0 |
| `candidate_uncertainty_proxy` | float | all | night | public | `compute_score_state` | 0.5 |
| `candidate_survival_proxy` | float | all | night | public | `build_candidate_feature_row` | 0.0 |
