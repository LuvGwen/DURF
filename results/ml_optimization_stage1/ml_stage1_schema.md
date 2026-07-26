# ML Stage 1 Dataset Schema

Rows are actor-candidate decision snapshots. Each decision state is expanded to one row per sampled legal candidate. Features are reconstructed from events available before the decision. True roles and final winner are label columns only.

## Pilot Scale

- `seeds`: `[42, 43, 44, 45, 46]`
- `games_per_seed`: `12`
- `generated_games`: `60`
- `max_candidates`: `6`
- `decision_limits`: `{'seer_check': 500, 'wolf_kill': 500, 'day_vote': 1000}`
- `rollout_counts`: `{'seer_check': 5, 'wolf_kill': 5, 'day_vote': 3}`
- `dataset_generation_runtime_seconds`: `0.7934751510620117`
- `python_version`: `3.14.3`

## Required Dataset Files

- `seer_check`: `results/ml_optimization_stage1/ml_seer_check_decision_dataset.csv`
- `wolf_kill`: `results/ml_optimization_stage1/ml_wolf_kill_decision_dataset.csv`
- `day_vote`: `results/ml_optimization_stage1/ml_vote_decision_dataset.csv`
- `identity`: `results/ml_optimization_stage1/ml_identity_prediction_dataset.csv`
- `splits`: `results/ml_optimization_stage1/ml_dataset_split_assignments.csv`
- `validation`: `results/ml_optimization_stage1/ml_dataset_validation_summary.csv`
- `rollout_summary`: `results/ml_optimization_stage1/ml_rollout_value_summary.csv`
- `schema`: `results/ml_optimization_stage1/ml_stage1_schema.md`
- `feature_registry`: `results/ml_optimization_stage1/ml_feature_registry.md`
- `limitations`: `results/ml_optimization_stage1/ml_stage1_limitations.md`

## Column Groups

- Identification columns: decision/game/split metadata.
- Feature columns: registered observation-safe values.
- Label columns: true role and outcome labels excluded from models.
- Rollout columns: offline action-value estimates.
