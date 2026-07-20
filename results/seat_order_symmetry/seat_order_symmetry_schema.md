# Seat-Order Symmetry Game-Level Schema

This dataset contains one row per completed 10-player game. Each base configuration is run twice: once with normal displayed seat labels and once with mirrored displayed labels. Stable physical seats preserve the underlying role assignment across each pair.

| column | data_type | description |
|---|---|---|
| pair_id | string | Shared identifier for a normal/mirrored pair. |
| game_id | string | Unique game identifier including orientation. |
| seed | integer | Top-level experimental seed. |
| base_game_index | integer | One-based paired base configuration index. |
| strategy | string | Seer checking strategy. |
| orientation | string | normal or mirrored displayed seat orientation. |
| mirrored | integer | 1 when the physical-to-displayed seat map is mirrored, else 0. |
| clockwise_direction | string | Whether displayed labels increase clockwise or counter-clockwise. |
| physical_to_displayed_seat_mapping | JSON object | Map from stable physical seat identity to displayed player_id. |
| physical_seer_seat | integer | Stable physical seat occupied by the seer. |
| displayed_seer_seat | integer | Displayed player_id occupied by the seer under this orientation. |
| physical_wolf_seats | JSON list | Stable physical seats occupied by wolves. |
| displayed_wolf_seats | JSON list | Displayed player_ids occupied by wolves under this orientation. |
| wolves_on_edge | integer | Number of wolves in displayed edge seats. |
| wolves_on_inner | integer | Number of wolves in displayed inner seats. |
| wolves_left_side | integer | Number of wolves on the displayed left side. |
| wolves_right_side | integer | Number of wolves on the displayed right side. |
| edge_has_wolf | integer | 1 if any displayed edge seat contains a wolf. |
| seer_on_edge | integer | 1 if the displayed seer seat is an edge seat. |
| seer_left_side | integer | 1 if the displayed seer seat is on the left side. |
| winner | string | Final winner: wolf, village, or draw. |
| village_win | integer | 1 if village won, otherwise 0. |
| wolf_win | integer | 1 if wolves won, otherwise 0. |
| total_rounds | integer | Final GameState round_number. |
| first_check_physical_target | integer | Physical seat checked by the first seer action. |
| first_check_displayed_target | integer | Displayed seat checked by the first seer action. |
| first_check_target_is_wolf | integer | 1 if first check found a wolf, 0 if not, blank if no check. |
| all_check_physical_targets | JSON list | All seer check targets converted to physical seats. |
| all_check_displayed_targets | JSON list | All seer check targets as displayed player_ids. |
| total_seer_checks | integer | Count of seer_check events. |
| found_wolf_by_check_1 | integer | 1 if a wolf was found within the first check. |
| found_wolf_by_check_2 | integer | 1 if a wolf was found within the first two checks. |
| found_wolf_by_check_3 | integer | 1 if a wolf was found within the first three checks. |
| checks_until_first_wolf | integer | Ordinal check that first found a wolf; blank if none. |
| seer_survived_to_game_end | integer | 1 if seer was alive at game end, otherwise 0. |
| seer_death_round | integer | Round in which the seer died; blank if survived. |
| strategy_direction_relative_to_physical_layout | string | How the displayed-label rule maps onto physical layout. |
| strategy_direction_relative_to_displayed_labels | string | How the rule behaves in displayed numeric labels. |
| first_target_physical_distance | integer | Circular distance between physical seer and first physical target. |
| first_target_displayed_order_rank | integer | First target rank in the strategy's displayed-seat ordering. |
