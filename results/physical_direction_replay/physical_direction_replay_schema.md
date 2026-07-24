# Physical Direction Replay Schema

The replay datasets use stable `actor_uid` values as physical identity. Physical seats can be mirrored without changing actor identity or role identity. Supplied actions target actor_uids and record physical target seats for auditability.

| column | description |
|---|---|
| experiment_component | A, B, or C replay experiment component. |
| pair_id | Stable pair identifier. |
| game_id | Stable game or pair identifier. |
| seed | Experiment seed. |
| base_game_index | One-based base physical configuration index. |
| reference_or_replay | Reference/replay pair label. |
| strategy | Seer checking strategy or strategy pair. |
| mirrored | 1 if the row uses a mirrored physical layout. |
| physical_direction | Physical direction condition. |
| actor_mapping | JSON actor_uid to role mapping. |
| physical_mapping | JSON actor_uid to physical seat mapping. |
| action_log_id | Captured supplied-action log identifier. |
| action_count | Number of supplied actions. |
| reference_action_count | Reference supplied-action count. |
| replay_action_count | Replay or comparison action count. |
| action_sequence_exact_match | 1 if action signatures match. |
| state_sequence_exact_match | 1 if replay state hashes match. |
| winner_match | 1 if winner matches. |
| total_rounds_match | 1 if total rounds match. |
| final_alive_set_match | 1 if final alive actor set matches. |
| first_divergence_event_index | First divergent action index. |
| first_divergence_round | First divergent action round. |
| first_divergence_phase | First divergent action phase. |
| first_divergence_type | First divergent action or hash type. |
| mirrored_action_sequence_match | 1 if mirrored strategy action signatures match after coordinate normalization. |
| first_check_mirror_match | 1 if the first seer check target actor mirrors correctly. |
| full_check_sequence_mirror_match | 1 if all seer check target actors mirror correctly. |
| vote_sequence_mirror_match | 1 if the full supplied vote sequence matches by actor_uid. |
| speech_sequence_mirror_match | 1 if speech actions match by actor_uid, speech type, target, and deception type. |
| winner_mirror_match | 1 if mirrored strategy pair winner matches. |
| rounds_mirror_match | 1 if mirrored strategy pair total rounds match. |
| final_alive_mirror_match | 1 if mirrored strategy pair final alive actor set matches. |
| winner | Reference game winner. |
| village_win | 1 if reference game winner is village. |
| wolf_win | 1 if reference game winner is wolf. |
| total_rounds | Reference game final round number. |
| seer_actor_uid | Stable actor_uid of the seer. |
| seer_survived_to_game_end | 1 if the seer actor survived to game end. |
| total_seer_checks | Number of seer_check actions. |
| found_wolf_by_check_1 | 1 if a wolf was found by check 1. |
| found_wolf_by_check_2 | 1 if a wolf was found by check 2. |
| found_wolf_by_check_3 | 1 if a wolf was found by check 3. |
