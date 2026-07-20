# Seat-Order Asymmetry Code Audit

This audit identifies code paths that may depend on numeric seat labels, player-list order, or deterministic tie-breaking. The symmetry experiment does not change these mechanisms; it measures whether they alter outcomes under mirrored labels.

| file | function or code path | behavior | likely bias |
|---|---|---|---|
| seer_action.py | choose_left_to_right_target | Sorts candidate player_id values in ascending order. | Favors lower displayed labels. |
| seer_action.py | choose_right_to_left_target | Sorts candidate player_id values in descending order. | Favors higher displayed labels. |
| seer_action.py | choose_alternate_sides_target | Uses displayed left/right side and tie-breaks by lower player_id. | Depends on displayed side labels and lower-seat tie-breaks. |
| seer_action.py | choose_nearest_first_target | Tie-breaks equal circular distances by lower player_id. | Favors lower displayed labels. |
| seer_action.py | choose_farthest_first_target | Tie-breaks equal circular distances by lower player_id. | Favors lower displayed labels. |
| seer_action.py | coverage_balanced, hybrid, information_gain_proxy | Use lower player_id as deterministic final tie-break. | Favors lower displayed labels when scores tie. |
| position_model.py | get_side, get_seat_type | Classifies side and edge/inner from numeric player_id. | Position labels are display-label dependent. |
| position_model.py | assign_random_roles_to_seats | Shuffles roles but applies side/seat_type by player_id. | Role is randomized, side remains numeric-seat based. |
| game.py | day_phase | Speech and voting iterate alive_players in game_state order. | Player list order can affect event order and tied decisions. |
| game_state.py | get_alive_players and related helpers | Return players in the original state.players order. | List order can propagate to downstream choices. |
| voting.py | choose_vote_target | Stable sort after score calculation. | Exact score ties favor earlier candidate order. |
| wolf_strategy.py | choose_wolf_kill_target | Stable sort after threat scoring. | Exact score ties favor earlier candidate order. |
| witch_action.py | perform_witch_poison | max by suspicion_score. | Exact score ties favor earlier candidate order. |
| hunter_action.py | perform_hunter_shot | max by suspicion_score. | Exact score ties favor earlier candidate order. |
| speech_action.py | build_speech_rng | Includes player_id in deterministic speech RNG seed. | Displayed numeric label can affect speech act randomness. |

## Critical Implementation Checks

- **Does any global mechanism iterate through players ascending seat-number order?** Yes. Player lists are usually stored and queried in ascending displayed player_id order in these experiments.
- **Does any tie-break favor lower seats?** Yes. Several deterministic seer strategies and some stable-sort or max paths favor lower displayed labels on exact ties.
- **Does any action order depend on the original player list?** Yes. Day speech, voting, and several candidate scans inherit game_state.players order.
- **Does left/right side classification depend asymmetrically on numeric labels?** Yes. Seats 1-5 are left and 6-10 are right.
- **Could player IDs affect RNG sequence or event resolution?** Yes. Speech RNG explicitly uses player_id and event order can follow player-list order.
- **Could mirroring change random number consumption?** The experiment seeds paired normal/mirrored games with the same game RNG seed, but different displayed labels can still change branch choices and therefore downstream consumption.
