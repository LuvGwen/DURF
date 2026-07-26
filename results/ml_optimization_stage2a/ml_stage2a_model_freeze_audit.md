# ML Stage 2A Model Freeze Audit

The frozen ridge wolf-kill model was serialized before live A/B execution.

| Field | Value |
| --- | --- |
| model_type | ridge_regression_stdlib_l2 |
| target_column | full_rollout_mean_team_win_rate |
| feature_count | 52 |
| training_rows | 120 |
| training_seeds | [42, 43, 44, 45, 46, 47, 48, 49] |
| validation_seeds | [50, 51] |
| excluded_stage15_final_test_seeds | [52, 53, 54, 55, 56] |
| live_final_test_seeds | [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119] |
| source_commit_hash | be2175d5e0b0be63a39ddfd9cc6066b2871d5024 |
| source_dataset_sha256 | e9e22ea70cbcfc8ac0b407559b434b1e736e193eab1e6f887b89d9f5ccfa7187 |
| model_artifact_hash | f3c5e60275eea04c4a03e15a21aab2713e86a4e2b446ff0fbf9b194e90ae124b |
| manifest_hash | 3636ee12b35a57bbe8811b59ccf2c37a2bfec25ced6170ee3f51615da6f64f83 |

Validation checks enforce coefficient count, feature order, standardization statistics, model artifact hash, manifest hash, and seed isolation.
