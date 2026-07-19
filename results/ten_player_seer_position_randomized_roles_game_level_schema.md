# Ten-Player Seer Position Randomized Roles Game-Level Schema

This dataset contains one row per completed game from the 10-player randomized-role seer-position experiment. List-like fields are serialized as compact JSON arrays.

| column | data_type | description | nullable | allowed_values_or_serialization |
|---|---|---|---|---|
| game_id | string | Unique strategy/seed/game identifier. | No | Plain text. |
| seed | integer | Random seed used for the run. | No | Plain text. |
| game_index_within_seed | integer | One-based game index for this seed and strategy. | No | Plain text. |
| strategy | string | Seer checking strategy. | No | One of the configured seer_check_strategy values. |
| winner | string | Final game winner. | No | Allowed values: wolf, village, draw. |
| village_win | integer | Indicator for village victory. | No | 1 if winner is village, otherwise 0. |
| wolf_win | integer | Indicator for wolf victory. | No | 1 if winner is wolf, otherwise 0. |
| seer_seat | integer | Seat number occupied by the seer. | Yes | Blank if no seer exists. |
| seer_side | string | Position-model side for the seer seat. | Yes | Allowed values: left, right, or blank. |
| seer_seat_type | string | Position-model seat type for the seer seat. | Yes | Allowed values: edge, inner, or blank. |
| wolf_seats | JSON list | Seat numbers occupied by wolves. | No | Serialized as a JSON array of integers. |
| wolves_on_edge | integer | Number of wolves in edge seats. | No | Computed from final seat-role assignment. |
| wolves_on_inner | integer | Number of wolves in inner seats. | No | Computed from final seat-role assignment. |
| wolves_left_side | integer | Number of wolves on the left side. | No | Computed from final seat-role assignment. |
| wolves_right_side | integer | Number of wolves on the right side. | No | Computed from final seat-role assignment. |
| first_check_target | integer | Seat checked by the first seer action. | Yes | Blank if no seer check occurred. |
| first_check_target_role | string | Role of the first checked target. | Yes | Blank if no seer check occurred. |
| first_check_target_is_wolf | integer | Whether the first checked target was a wolf. | Yes | 1 for true, 0 for false, blank if no seer check occurred. |
| first_check_target_seat_type | string | Seat type of the first checked target. | Yes | Allowed values: edge, inner, or blank. |
| first_check_target_side | string | Side of the first checked target. | Yes | Allowed values: left, right, or blank. |
| all_seer_check_targets_in_order | JSON list | All seer check targets in event-log order. | No | Serialized as a JSON array of integers. |
| all_seer_check_roles_in_order | JSON list | Roles checked by the seer in event-log order. | No | Serialized as a JSON array of strings. |
| total_seer_checks | integer | Number of seer_check events in the game. | No | Plain text. |
| seer_found_any_wolf | integer | Whether any seer check found a wolf. | No | 1 for true, 0 for false. |
| seer_found_wolf_count | integer | Number of seer checks that found wolves. | No | Plain text. |
| first_check_wolf | integer | Whether the first seer check found a wolf. | Yes | 1 for true, 0 for false, blank if no seer check occurred. |
| seer_survived_to_game_end | integer | Whether the seer was alive at game end. | Yes | 1 for true, 0 for false, blank if no seer exists. |
| seer_death_round | integer | Round in which the seer died. | Yes | Blank if the seer survived or no seer exists. |
| total_rounds | integer | Final round_number from GameState summary. | No | Plain text. |
| final_alive_players | integer | Number of alive players at game end. | No | Plain text. |
| final_alive_wolves | integer | Number of alive wolves at game end. | No | Plain text. |
| final_alive_villagers | integer | Number of alive village-team players at game end. | No | Plain text. |
