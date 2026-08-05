# R8 Sample Unit Audit

| Unit | Independence | Summable | Rule |
| --- | --- | --- | --- |
| independent_complete_game | clustered when matched or seeded | no | Report stage-level game counts and independent unit; do not claim a single project-wide independent N. |
| matched_configuration_set | matched | no | Matched policy games are not independent observations; analyze policy differences within matched sets. |
| seed | cluster label | no | Use seed-level robustness within each experiment. |
| behavioral_regime | cluster or stratification variable | no | Use as robustness strata, not independent sample size. |
| player_game_row | clustered within game | no | Player rows from the same game are clustered. |
| action_event | nested within games | no | Event rows are not independent games. |
| speech_utterance | nested within game, speaker, template, and condition | no | Utterances are not independent game outcomes. |
| vote_event | nested within games and policies | no | Vote rows are mechanism diagnostics, not independent games. |
| belief_update | nested within game and target | no | Use for mechanism diagnosis, not final win-rate inference. |
| rollout_branch | nested within source decision state | no | Rollout branches are not live games. |
| counterfactual_candidate_action | nested within decision state | no | Candidate rows are not independent games. |
| literature_source | bibliography item | yes_as_bibliography_inventory_only | Literature sources are not empirical samples. |
| finding_literature_mapping | claim-support mapping | no | Literature mapping rows are not empirical samples. |
