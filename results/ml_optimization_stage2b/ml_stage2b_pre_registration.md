# ML Stage 2B Pre-Registration

Primary outcome: `wolf_win` in matched complete games.

Primary contrasts:

- `ml_first_kill_only` vs `existing_rule`
- `ml_first_two_kills` vs `existing_rule`
- `continuous_frozen_ml` vs `existing_rule`
- `selective_ml_override` vs `existing_rule`

Multiplicity control: Holm correction across the four primary contrasts.

Development seeds: 200, 201, 202, 203, 204, 205, 206, 207, 208, 209

Validation seeds: 210, 211, 212, 213, 214

Final-test seeds: 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239

Final-test seeds are excluded from threshold selection and model training.

Policies: existing_rule, ml_first_kill_only, ml_single_random_kill, ml_first_two_kills, continuous_frozen_ml, existing_with_ml_shadow, selective_ml_override, high_confidence_shadow

Behavioral regimes: baseline_speech_enabled, speech_disabled, herding_enabled, deception_enabled, heterogeneous_risk_preference, strong_village_information, weak_village_information, mixed_seer_strategy, mixed_voting_strategy, mixed_wolf_deception_strategy

The frozen Stage 2A model is not retrained in Stage 2B. The selective
override rule is calibrated from development/validation shadow decisions
and then frozen before final-test live evaluation.
