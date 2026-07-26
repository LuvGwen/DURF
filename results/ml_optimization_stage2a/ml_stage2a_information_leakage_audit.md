# ML Stage 2A Information Leakage Audit

| Check | Status |
| --- | --- |
| No true role columns in live feature matrix | PASS |
| No target label columns in live feature matrix | PASS |
| No future outcome columns | PASS |
| No final survival columns | PASS |
| No full-rollout value columns at live inference time | PASS |
| No target special-role truth in live feature order | PASS |
| No hidden village role identity in live feature order | PASS |
| No unobserved witch-state features | PASS |
| No unobserved hunter-state features | PASS |
| Frozen manifest validates against the current feature order | PASS |

Posthoc role fields are present in raw analysis outputs only; they are excluded from the frozen live feature order used by the policy. The live model feature count is 52.

Feature order hash validation is enforced by `validate_frozen_model_manifest()`.

Live feature columns:

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
