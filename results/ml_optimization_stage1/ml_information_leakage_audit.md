# ML Stage 1 Information Leakage Audit

Overall result: PASS

| check | passed | detail |
|---|---:|---|
| no_true_role_or_winner_in_feature_columns | 1 | Feature registry excludes label/prohibited columns. |
| labels_not_features | 1 | Overlap: [] |
| no_future_feature_columns | 1 | Future columns: [] |
| seer_private_information_only_visible_to_seer | 1 | Unsafe rows: 0 |
| wolf_teammate_identity_only_visible_to_wolves_or_seer_checks | 1 | Unsafe rows: 0 |
| village_actors_receive_no_wolf_team_information | 1 | Unsafe rows: 0 |
| unused_special_abilities_of_others_hidden | 1 | Special-role leakage columns: [] |
| train_test_groups_do_not_overlap | 1 | Conflicts: [] |
| duplicate_label_condition_rows_stay_in_one_split | 1 | Conflicts: 0 |
| feature_availability_rules_enforced | 1 | Potential issues: 0 |
| rollout_action_selection_uses_observable_rows | 1 | Rollout evaluator receives one candidate row and returns values; model feature matrix excludes labels. |
| model_serialization_excludes_prohibited_metadata | 1 | Serialized stdlib models contain only feature names, intercepts, and weights. |
