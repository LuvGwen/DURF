# R6.1 Dataset Schema

## Game-Level Raw Files

| Column | Description |
|---|---|
| module | Complete-game matched outcome or diagnostic metric. |
| policy | Complete-game matched outcome or diagnostic metric. |
| matched_set_id | Complete-game matched outcome or diagnostic metric. |
| seed | Complete-game matched outcome or diagnostic metric. |
| seed_split | Complete-game matched outcome or diagnostic metric. |
| behavioral_regime | Complete-game matched outcome or diagnostic metric. |
| replicate_index | Complete-game matched outcome or diagnostic metric. |
| game_seed | Complete-game matched outcome or diagnostic metric. |
| game_id | Complete-game matched outcome or diagnostic metric. |
| winner | Complete-game matched outcome or diagnostic metric. |
| village_win | Complete-game matched outcome or diagnostic metric. |
| wolf_win | Complete-game matched outcome or diagnostic metric. |
| draw | Complete-game matched outcome or diagnostic metric. |
| round_number | Complete-game matched outcome or diagnostic metric. |
| num_alive_players | Complete-game matched outcome or diagnostic metric. |
| num_events | Complete-game matched outcome or diagnostic metric. |
| actor_role | Complete-game matched outcome or diagnostic metric. |
| actor_payoff | Complete-game matched outcome or diagnostic metric. |
| team_payoff | Complete-game matched outcome or diagnostic metric. |
| wolf_payoff | Complete-game matched outcome or diagnostic metric. |
| village_payoff | Complete-game matched outcome or diagnostic metric. |
| actor_negative_payoff | Complete-game matched outcome or diagnostic metric. |
| total_seer_checks | Complete-game matched outcome or diagnostic metric. |
| seer_reveals | Complete-game matched outcome or diagnostic metric. |
| hunter_shots | Complete-game matched outcome or diagnostic metric. |
| hunter_abstentions | Complete-game matched outcome or diagnostic metric. |
| witch_saves | Complete-game matched outcome or diagnostic metric. |
| witch_poison | Complete-game matched outcome or diagnostic metric. |
| night_kills_prevented | Complete-game matched outcome or diagnostic metric. |
| wolf_deceptions | Complete-game matched outcome or diagnostic metric. |
| false_accusations | Complete-game matched outcome or diagnostic metric. |
| deflections | Complete-game matched outcome or diagnostic metric. |
| trust_building_deceptions | Complete-game matched outcome or diagnostic metric. |
| credibility_costs | Complete-game matched outcome or diagnostic metric. |
| self_defense_costs | Complete-game matched outcome or diagnostic metric. |
| wrong_accusation_penalties | Complete-game matched outcome or diagnostic metric. |
| day_votes | Complete-game matched outcome or diagnostic metric. |
| wrong_eliminations | Complete-game matched outcome or diagnostic metric. |
| correct_vote_count | Complete-game matched outcome or diagnostic metric. |
| wrong_vote_count | Complete-game matched outcome or diagnostic metric. |
| first_seer_check_wolf | Complete-game matched outcome or diagnostic metric. |
| found_wolf_by_check_2 | Complete-game matched outcome or diagnostic metric. |
| found_wolf_by_check_3 | Complete-game matched outcome or diagnostic metric. |
| seer_survived | Complete-game matched outcome or diagnostic metric. |
| wolves_discovered | Complete-game matched outcome or diagnostic metric. |
| mean_checks_until_first_wolf | Complete-game matched outcome or diagnostic metric. |
| no_wolf_found | Complete-game matched outcome or diagnostic metric. |
| search_path_coverage | Complete-game matched outcome or diagnostic metric. |
| seer_total_checks | Complete-game matched outcome or diagnostic metric. |
| seat_assignment_signature | Complete-game matched outcome or diagnostic metric. |

## Action Raw Files

| Column | Description |
|---|---|
| module | Role action event field for diagnostic analysis. |
| policy | Role action event field for diagnostic analysis. |
| matched_set_id | Role action event field for diagnostic analysis. |
| seed | Role action event field for diagnostic analysis. |
| behavioral_regime | Role action event field for diagnostic analysis. |
| game_id | Role action event field for diagnostic analysis. |
| event_index | Role action event field for diagnostic analysis. |
| event_type | Role action event field for diagnostic analysis. |
| round | Role action event field for diagnostic analysis. |
| phase | Role action event field for diagnostic analysis. |
| actor_id | Role action event field for diagnostic analysis. |
| target_id | Role action event field for diagnostic analysis. |
| target_role | Role action event field for diagnostic analysis. |
| target_is_wolf | Role action event field for diagnostic analysis. |
| action_subtype | Role action event field for diagnostic analysis. |
| success | Role action event field for diagnostic analysis. |
| extra_json | Role action event field for diagnostic analysis. |

Action rows are diagnostics and are not independent complete-game samples. Formal primary contrasts use `matched_set_id` as the paired game unit.
