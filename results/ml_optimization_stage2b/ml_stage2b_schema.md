# ML Stage 2B Schema

## Primary Raw Files

- `stage2b_live_game_level_raw.csv`: one row per completed live game.
- `stage2b_live_decision_raw.csv`: one row per wolf-kill decision.
- `stage2b_policy_prediction_raw.csv`: one row per legal candidate at each wolf-kill decision.
- `stage2b_single_intervention_rollout_raw.csv`: one row per forced branch rollout.
- `stage2b_distribution_shift_trajectory_raw.csv`: one row per decision with cumulative shift fields.
- `stage2b_hybrid_ranking_diagnostic_raw.csv`: one row per decision comparing ML, rule, and hybrid rankings.
- `stage2b_downstream_mechanism_raw.csv`: one row per decision with target role and downstream event outcomes.
- `stage2b_seed_registry.csv`: seed split and allowed-use registry.

## Independent Unit

Primary live-policy inference uses matched complete games grouped by
`matched_set_id`. Candidate and decision rows are mechanism diagnostics and
are not treated as independent games.

## Key Fields

- `policy_name`: Stage 2B live condition.
- `stage2b_executed_ml_intervention`: whether the frozen ML target was executed.
- `prior_ml_interventions`: number of earlier executed ML interventions in that game.
- `distribution_shift_category`: selected-target shift category from Stage 2A metrics.
- `top_two_predicted_value_margin`: ML top-one minus top-two predicted value.
- `ml_advantage_over_existing`: ML top predicted value minus existing target predicted value.
- `selective_override_qualified`: whether the frozen selective rule would override.
