# Distribution Sensitivity

| Axis | Status | Risk |
| --- | --- | --- |
| seed | adequate_for_internal_robustness | moderate |
| behavioral_regime | adequate_for_internal_robustness | moderate |
| role_setup | limited_external_generalization | high |
| speech_templates | template_bound | high |
| seat_role_assignment | validated_for_position_claims | low |
| physical_direction | engine_symmetry_validated | low |
| strategy_space | not_global_optimization | high |

| Domain | Severity | Mitigation |
| --- | --- | --- |
| fixed role count | high | R9 or R8.2 should replicate load-bearing policies under preregistered role setups. |
| generated speech | high | Do not claim natural-language deployment. |
| behavioral regimes | moderate | Report leave-one-regime-out and avoid external claims. |
| policy search | high | Use corrected labels and targeted replication. |
| payoff coefficients | moderate | Report sensitivity and default retention rules. |
