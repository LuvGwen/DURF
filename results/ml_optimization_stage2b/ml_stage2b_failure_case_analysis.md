# ML Stage 2B Failure Case Analysis

| Matched Set | Policy | Seed | Regime | Round | Selected Role | Shift | Margin | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_first_kill_only | 220 | baseline_speech_enabled | 1 | villager | in_distribution | 0.0060 | low_margin_decision |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_first_kill_only | 220 | baseline_speech_enabled | 2 | seer | mild_shift | 0.0019 | low_margin_decision |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_first_kill_only | 220 | baseline_speech_enabled | 3 | hunter | strong_shift | 0.0004 | strong_distribution_shift |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_first_kill_only | 220 | baseline_speech_enabled | 4 | villager | strong_shift | 0.0132 | strong_distribution_shift |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_single_random_kill | 220 | baseline_speech_enabled | 1 | seer | in_distribution | 0.0060 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_single_random_kill | 220 | baseline_speech_enabled | 2 | hunter | strong_shift | 0.0019 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_single_random_kill | 220 | baseline_speech_enabled | 3 | seer | strong_shift | 0.0038 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_single_random_kill | 220 | baseline_speech_enabled | 4 | villager | strong_shift | 0.0192 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_first_two_kills | 220 | baseline_speech_enabled | 1 | villager | in_distribution | 0.0060 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_first_two_kills | 220 | baseline_speech_enabled | 2 | hunter | strong_shift | 0.0019 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_first_two_kills | 220 | baseline_speech_enabled | 3 | seer | strong_shift | 0.0038 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | ml_first_two_kills | 220 | baseline_speech_enabled | 4 | villager | strong_shift | 0.0192 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | continuous_frozen_ml | 220 | baseline_speech_enabled | 1 | villager | in_distribution | 0.0060 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | continuous_frozen_ml | 220 | baseline_speech_enabled | 2 | hunter | strong_shift | 0.0019 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | continuous_frozen_ml | 220 | baseline_speech_enabled | 3 | villager | strong_shift | 0.0038 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | continuous_frozen_ml | 220 | baseline_speech_enabled | 4 | seer | strong_shift | 0.0209 | policy_lost_existing_won |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | existing_with_ml_shadow | 220 | baseline_speech_enabled | 1 | seer | in_distribution | 0.0060 | low_margin_decision |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | existing_with_ml_shadow | 220 | baseline_speech_enabled | 2 | seer | mild_shift | 0.0019 | low_margin_decision |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | existing_with_ml_shadow | 220 | baseline_speech_enabled | 3 | hunter | strong_shift | 0.0004 | strong_distribution_shift |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | existing_with_ml_shadow | 220 | baseline_speech_enabled | 4 | villager | strong_shift | 0.0132 | strong_distribution_shift |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | selective_ml_override | 220 | baseline_speech_enabled | 1 | seer | in_distribution | 0.0060 | low_margin_decision |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | selective_ml_override | 220 | baseline_speech_enabled | 2 | seer | mild_shift | 0.0019 | low_margin_decision |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | selective_ml_override | 220 | baseline_speech_enabled | 3 | hunter | strong_shift | 0.0004 | strong_distribution_shift |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | selective_ml_override | 220 | baseline_speech_enabled | 4 | villager | strong_shift | 0.0132 | strong_distribution_shift |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | high_confidence_shadow | 220 | baseline_speech_enabled | 1 | seer | in_distribution | 0.0060 | low_margin_decision |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | high_confidence_shadow | 220 | baseline_speech_enabled | 2 | seer | mild_shift | 0.0019 | low_margin_decision |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | high_confidence_shadow | 220 | baseline_speech_enabled | 3 | hunter | strong_shift | 0.0004 | strong_distribution_shift |
| stage2b_seed_220_base_1_regime_baseline_speech_enabled | high_confidence_shadow | 220 | baseline_speech_enabled | 4 | villager | strong_shift | 0.0132 | strong_distribution_shift |
| stage2b_seed_220_base_1_regime_speech_disabled | ml_first_kill_only | 220 | speech_disabled | 1 | villager | mild_shift | 0.0149 | low_margin_decision |
| stage2b_seed_220_base_1_regime_speech_disabled | ml_first_kill_only | 220 | speech_disabled | 2 | seer | mild_shift | 0.0046 | low_margin_decision |
