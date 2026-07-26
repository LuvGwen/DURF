# ML Stage 2A Failure Case Analysis

Failure-case rows written: 200. Rows are defined as non-control policy decisions where the existing rule won but the policy lost, or where the selected candidate was marked as a strong distribution-shift case.

| Matched Set | Policy | Seed | Regime | Round | Selected Target | Selected Role | Existing Target | Shift | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seed_100_base_1_regime_baseline_speech_enabled | frozen_ml | 100 | baseline_speech_enabled | 3 | 3 | villager | 6 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_baseline_speech_enabled | frozen_ml | 100 | baseline_speech_enabled | 4 | 4 | villager | 6 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_baseline_speech_enabled | frozen_hybrid_50_50 | 100 | baseline_speech_enabled | 2 | 3 | villager | 6 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_baseline_speech_enabled | frozen_hybrid_50_50 | 100 | baseline_speech_enabled | 4 | 4 | villager | 6 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_baseline_speech_enabled | frozen_ml_epsilon_010 | 100 | baseline_speech_enabled | 3 | 3 | villager | 6 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_baseline_speech_enabled | frozen_ml_epsilon_010 | 100 | baseline_speech_enabled | 4 | 4 | villager | 6 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_speech_disabled | frozen_ml | 100 | speech_disabled | 2 | 7 | villager | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_speech_disabled | frozen_ml | 100 | speech_disabled | 3 | 1 | witch | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_speech_disabled | frozen_hybrid_50_50 | 100 | speech_disabled | 2 | 7 | villager | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_speech_disabled | frozen_hybrid_50_50 | 100 | speech_disabled | 3 | 1 | witch | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_speech_disabled | frozen_ml_epsilon_010 | 100 | speech_disabled | 2 | 7 | villager | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_speech_disabled | frozen_ml_epsilon_010 | 100 | speech_disabled | 3 | 1 | witch | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_herding_enabled | frozen_ml | 100 | herding_enabled | 2 | 7 | hunter | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_herding_enabled | frozen_ml | 100 | herding_enabled | 3 | 3 | seer | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_herding_enabled | frozen_hybrid_50_50 | 100 | herding_enabled | 1 | 7 | hunter | 3 | mild_shift | policy_lost_existing_won |
| seed_100_base_1_regime_herding_enabled | frozen_hybrid_50_50 | 100 | herding_enabled | 2 | 4 | villager | 3 | strong_shift | policy_lost_existing_won |
| seed_100_base_1_regime_herding_enabled | frozen_hybrid_50_50 | 100 | herding_enabled | 3 | 4 | villager | 3 | strong_shift | policy_lost_existing_won |
| seed_100_base_1_regime_herding_enabled | frozen_ml_epsilon_010 | 100 | herding_enabled | 3 | 7 | hunter | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_herding_enabled | frozen_ml_epsilon_010 | 100 | herding_enabled | 4 | 3 | seer | 3 | strong_shift | strong_distribution_shift |
| seed_100_base_1_regime_deception_enabled | frozen_ml | 100 | deception_enabled | 2 | 7 | villager | 1 | strong_shift | strong_distribution_shift |
