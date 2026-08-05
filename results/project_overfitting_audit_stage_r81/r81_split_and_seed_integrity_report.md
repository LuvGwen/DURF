# Split and Seed Integrity

Final-seed reuse is classified as post-test model/policy selection rather than raw gameplay leakage.

| Unit | Status | Risk |
| --- | --- | --- |
| game | pass | controlled |
| matched_set | pass | controlled |
| seed | pass_with_selection_caveat | controlled |
| behavioral_regime | pass | controlled |
| player | pass | controlled |
| event | pass | controlled |
| utterance/template | pass_with_caveat | controlled |
| ml_rollout | pass_with_caveat | controlled |
| policy_final_selection | selection_risk_found | post_selection_bias |

| Seed | Split | Reuse |
| --- | --- | --- |
| 500 | development | development_or_diagnostic |
| 501 | development | development_or_diagnostic |
| 502 | development | development_or_diagnostic |
| 503 | development | development_or_diagnostic |
| 504 | development | development_or_diagnostic |
| 505 | development | development_or_diagnostic |
| 506 | development | development_or_diagnostic |
| 507 | development | development_or_diagnostic |
| 508 | development | development_or_diagnostic |
| 509 | development | development_or_diagnostic |
