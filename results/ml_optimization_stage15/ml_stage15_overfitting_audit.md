# ML Stage 1.5 Overfitting Audit

Rows with overfitting flag: 1

| task | context | model | flag | classification |
|---|---|---|---:|---|
| identity | seer_candidate_states | existing_p_wolf | 0 | promising but uncertain |
| identity | seer_candidate_states | existing_suspicion | 0 | promising but uncertain |
| identity | seer_candidate_states | logistic_regression_stdlib | 1 | overfit |
| identity | village_vote_candidate_states | existing_p_wolf | 0 | promising but uncertain |
| identity | village_vote_candidate_states | existing_suspicion | 0 | promising but uncertain |
| identity | village_vote_candidate_states | logistic_regression_stdlib | 0 | promising but uncertain |
| action_value | seer_check | mean_baseline | 0 | promising but uncertain |
| action_value | seer_check | ridge_regression_stdlib | 0 | promising but uncertain |
| action_value | wolf_kill | mean_baseline | 0 | promising but uncertain |
| action_value | wolf_kill | ridge_regression_stdlib | 0 | promising but uncertain |
| action_value | day_vote | mean_baseline | 0 | promising but uncertain |
| action_value | day_vote | ridge_regression_stdlib | 0 | promising but uncertain |
