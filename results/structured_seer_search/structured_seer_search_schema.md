# Structured Seer Search Game-Level Schema

This dataset contains one row per completed 10-player randomized-role game. List-like fields use compact JSON serialization. `search_path_coverage_score` is defined as `unique_checked_targets / 9`, because the seer has nine possible non-self targets in a 10-player game.

## Strategy Definitions

- `random`: Randomly chooses among alive, unchecked, non-self targets.
- `default`: Uses the existing default random seer strategy, with the structured experiment repeat guard enabled.
- `edge_first`: Uses the existing edge-first positional strategy.
- `inner_first`: Uses the existing inner-first positional strategy.
- `highest_p_wolf`: Checks the alive unchecked player with the highest current p_wolf.
- `highest_suspicion`: Checks the alive unchecked player with the highest suspicion_score.
- `left_to_right`: Checks alive unchecked targets in increasing seat-number order.
- `right_to_left`: Checks alive unchecked targets in decreasing seat-number order.
- `alternate_sides`: Alternates between the side opposite the seer and the seer's own side. Ties are broken by nearest circular distance, then lower seat.
- `nearest_first`: Checks the alive unchecked target with minimum circular distance from the seer's seat.
- `farthest_first`: Checks the alive unchecked target with maximum circular distance from the seer's seat.
- `coverage_balanced`: Chooses the unchecked target that maximizes distance from already checked seats, then distance from the seer, then lower seat.
- `hybrid_suspicion_position`: Scores targets as suspicion_score + 0.25 * coverage_bonus.
- `information_gain_proxy`: Uses a visible-information proxy: 0.35 * unseen-side bonus + 0.25 * unseen-seat-type bonus + 0.25 * normalized distance + 0.15 * average(p_wolf, suspicion_score).

## Columns

| column | description |
|---|---|
| game_id | Unique strategy/seed/game identifier. |
| seed | Random seed used for this run. |
| game_index_within_seed | One-based game index within seed. |
| strategy | Seer search strategy. |
| winner | Final game winner: wolf, village, or draw. |
| village_win | Indicator for village victory. |
| wolf_win | Indicator for wolf victory. |
| total_rounds | Final GameState round number. |
| seer_seat | Seat number occupied by the seer. |
| seer_side | Seer's side from the position model. |
| seer_seat_type | Seer's edge/inner seat type. |
| wolf_seats | JSON list of wolf seat ids. |
| wolves_on_edge | Number of wolves in edge seats. |
| wolves_on_inner | Number of wolves in inner seats. |
| wolves_left_side | Number of wolves on the left side. |
| wolves_right_side | Number of wolves on the right side. |
| first_check_target | First seer check target seat. |
| first_check_target_role | Role of first checked target. |
| first_check_target_is_wolf | Indicator that first checked target was a wolf. |
| first_check_target_distance_from_seer | Circular seat distance from seer to first target. |
| first_check_target_seat_type | Seat type of first checked target. |
| all_seer_check_targets_in_order | JSON list of checked seats in event-log order. |
| all_seer_check_roles_in_order | JSON list of checked roles in event-log order. |
| all_seer_check_distances_in_order | JSON list of circular distances in event-log order. |
| total_seer_checks | Number of seer_check events. |
| first_check_wolf | Same as first_check_target_is_wolf. |
| found_wolf_by_check_1 | Indicator that a wolf was found by check 1. |
| found_wolf_by_check_2 | Indicator that a wolf was found by check 2. |
| found_wolf_by_check_3 | Indicator that a wolf was found by check 3. |
| checks_until_first_wolf | One-based check index for first wolf found; blank if none. |
| seer_found_any_wolf | Indicator that any checked target was wolf. |
| seer_found_wolf_count | Number of checked wolves. |
| unique_seat_types_checked | Number of distinct checked seat types. |
| unique_sides_checked | Number of distinct checked sides. |
| mean_pairwise_distance_between_checked_targets | Mean circular distance among checked target pairs. |
| search_path_coverage_score | unique_checked_targets / 9. |
| seer_survived_to_game_end | Indicator that seer survived. |
| seer_death_round | Round in which seer died; blank if alive. |
| final_alive_players | Final number of alive players. |
| final_alive_wolves | Final number of alive wolves. |
| final_alive_villagers | Final number of alive village-team players. |
