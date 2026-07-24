# Seat-Order-Neutral Game-Level Schema

This dataset contains one row per completed 10-player game in seat-order-neutral mode. `actor_uid` identifies the stable physical actor, `physical_seat` identifies circular layout position, and `displayed_player_id` is the visible numeric label. Normal, mirrored, and rotated displayed labels share the same physical role assignment and neutral actor iteration order.

| column | description |
|---|---|
| matched_set_id | Shared identifier for matched label conditions. |
| pair_id | Alias for matched_set_id for compatibility. |
| game_id | Unique completed-game identifier. |
| seed | Experimental seed. |
| base_game_index | One-based base configuration index. |
| strategy | Neutral seer checking strategy. |
| label_condition | normal, mirrored, or rotated displayed labels. |
| mirrored | 1 for mirrored label map. |
| rotation_offset | Circular displayed-label offset for rotated runs. |
| neutral_mode_enabled | 1 when neutral engine mode is active. |
| actor_uid_to_physical_seat | JSON map from actor_uid to physical seat. |
| actor_uid_to_displayed_id | JSON map from actor_uid to displayed id. |
| physical_to_displayed_mapping | JSON physical-to-displayed map. |
| displayed_to_physical_mapping | JSON displayed-to-physical map. |
| neutral_actor_iteration_order | JSON actor_uid order used by the engine. |
| seer_actor_uid | Stable actor_uid of the seer. |
| physical_seer_seat | Physical seer seat. |
| displayed_seer_id | Displayed player_id of the seer. |
| wolf_actor_uids | JSON list of wolf actor_uids. |
| physical_wolf_seats | JSON list of physical wolf seats. |
| displayed_wolf_ids | JSON list of displayed wolf ids. |
| wolves_on_edge | Number of physical edge seats occupied by wolves. |
| wolves_on_inner | Number of physical inner seats occupied by wolves. |
| wolves_left_side | Number of wolves on physical left side. |
| wolves_right_side | Number of wolves on physical right side. |
| edge_has_wolf | 1 if any physical edge seat contains a wolf. |
| seer_on_edge | 1 if the physical seer seat is an edge seat. |
| seer_left_side | 1 if the physical seer seat is on the left side. |
| strategy_direction_physical | Physical interpretation of strategy. |
| strategy_direction_displayed | Displayed-label interpretation. |
| first_check_actor_uid | Actor_uid checked first by seer. |
| first_check_physical_target | Physical first-check target. |
| first_check_displayed_target | Displayed first-check target. |
| all_check_actor_uids | JSON actor_uid check sequence. |
| all_check_physical_targets | JSON physical check sequence. |
| all_check_displayed_targets | JSON displayed check sequence. |
| total_seer_checks | Number of seer_check events. |
| first_check_target_is_wolf | 1 if first check found a wolf. |
| found_wolf_by_check_1 | 1 if wolf found by first check. |
| found_wolf_by_check_2 | 1 if wolf found by second check. |
| found_wolf_by_check_3 | 1 if wolf found by third check. |
| checks_until_first_wolf | Check index of first wolf; blank if none. |
| no_wolf_found | 1 if the seer never checked a wolf. |
| seer_found_wolf_count | Number of wolf checks in game. |
| seer_survived_to_game_end | 1 if seer survived. |
| seer_death_round | Round where seer died; blank if alive. |
| search_path_coverage_score | unique physical targets / 9. |
| winner | Final winner. |
| village_win | 1 for village victory. |
| wolf_win | 1 for wolf victory. |
| total_rounds | Final round number. |
| final_alive_players | Final alive-player count. |
| final_alive_wolves | Final alive wolf count. |
| final_alive_villagers | Final alive village-team count. |
| physical_first_target_matches_reference | 1 if first physical target matches normal-label reference. |
| physical_check_sequence_matches_reference_until_divergence | 1 if full physical check sequence matches normal reference. |
| first_divergence_round | First physicalized event divergence round. |
| first_divergence_phase | First physicalized event divergence phase. |
| first_divergence_event_type | First divergent event type. |
| paired_outcome_agreement | 1 if winner matches normal reference. |
| physical_final_alive_set_matches | 1 if final physical alive set matches normal reference. |
| role_assignment_seed | Stable role-assignment sub-seed. |
| speech_subseed_scheme | Documented speech sub-seed scheme. |
| strategy_subseed_scheme | Documented strategy sub-seed scheme. |
| tie_break_scheme | Documented neutral tie-break scheme. |
| main_game_seed | Main game RNG seed for this matched set. |
