# ML Stage 2A Pre-Registration

Primary outcome: `wolf_win`.

Primary contrasts:

- `frozen_ml` vs `existing_rule`
- `frozen_hybrid_50_50` vs `existing_rule`
- `frozen_ml_epsilon_010` vs `existing_rule`

Multiplicity control: Holm correction across the three primary contrasts.

Frozen policies:

- `existing_rule`
- `frozen_ml`
- `frozen_hybrid_50_50`
- `frozen_ml_epsilon_010`

Development seeds: [42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56]

Stage 2A shadow-validation seeds: [60, 61, 62, 63, 64]

Stage 2A final live-test seeds: [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119]

Live-test seeds are not used for model training, feature selection, model
selection, hybrid-weight tuning, epsilon tuning, or threshold tuning.

Behavioral regimes:

- `baseline_speech_enabled`: speech=True, herding=False, deception=False, risk=disabled, seer=information_gain_proxy, vote=suspicion_based
- `speech_disabled`: speech=False, herding=False, deception=False, risk=disabled, seer=information_gain_proxy, vote=suspicion_based
- `herding_enabled`: speech=True, herding=True, deception=False, risk=disabled, seer=highest_p_wolf, vote=suspicion_based
- `deception_enabled`: speech=True, herding=True, deception=True, risk=disabled, seer=information_gain_proxy, vote=suspicion_based
- `heterogeneous_risk_preference`: speech=True, herding=True, deception=True, risk=role_based, seer=coverage_balanced, vote=suspicion_based
- `strong_village_information`: speech=True, herding=True, deception=False, risk=disabled, seer=information_gain_proxy, vote=suspicion_based
- `weak_village_information`: speech=False, herding=False, deception=False, risk=disabled, seer=random, vote=random
- `mixed_seer_strategy`: speech=True, herding=True, deception=False, risk=disabled, seer=coverage_balanced, vote=suspicion_based
- `mixed_voting_strategy`: speech=True, herding=False, deception=False, risk=disabled, seer=highest_suspicion, vote=random
- `mixed_wolf_deception_strategy`: speech=True, herding=True, deception=True, risk=disabled, seer=information_gain_proxy, vote=suspicion_based

Hybrid weight is fixed at 0.50. Epsilon is fixed at 0.10.

This is a complete-game live A/B pilot. The actual scale is reported in
`ml_stage2a_experiment_report.md`.
