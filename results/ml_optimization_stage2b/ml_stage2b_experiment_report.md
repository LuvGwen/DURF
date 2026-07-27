# ML Stage 2B Experiment Report

## Overview

Stage 2B diagnoses why the frozen Stage 2A wolf-kill model looked useful in
shadow/full-rollout settings but underperformed when inserted into live
complete-game control.

## Data Scale

- Live complete games: 1600
- Independent matched sets: 200
- Wolf-kill decisions: 5428
- Seeds: 20
- Behavioral regimes: 10
- Frozen manifest hash: `3636ee12b35a57bbe8811b59ccf2c37a2bfec25ced6170ee3f51615da6f64f83`
- Frozen model artifact hash: `f3c5e60275eea04c4a03e15a21aab2713e86a4e2b446ff0fbf9b194e90ae124b`

## Policy Summary

| Policy | Games | Wolf Win | Village Win | Avg Rounds | Avg ML Interventions | Strong Shift Rate |
| --- | --- | --- | --- | --- | --- | --- |
| existing_rule | 200 | 71.00% | 29.00% | 3.4100 | 0.0000 | 57.25% |
| ml_first_kill_only | 200 | 72.00% | 28.00% | 3.4200 | 1.0000 | 57.11% |
| ml_single_random_kill | 200 | 66.50% | 33.50% | 3.3500 | 0.9700 | 55.01% |
| ml_first_two_kills | 200 | 63.00% | 37.00% | 3.3750 | 2.0000 | 54.53% |
| continuous_frozen_ml | 200 | 61.00% | 39.00% | 3.3450 | 3.3450 | 54.22% |
| existing_with_ml_shadow | 200 | 71.00% | 29.00% | 3.4100 | 0.0000 | 57.25% |
| selective_ml_override | 200 | 70.00% | 30.00% | 3.4200 | 0.1850 | 57.11% |
| high_confidence_shadow | 200 | 71.00% | 29.00% | 3.4100 | 0.0000 | 57.25% |

## Primary Matched Contrasts

| Contrast | Matched Sets | Diff | CI Low | CI High | Discordant OR | Raw p | Holm p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ml_first_kill_only_vs_existing_rule | 200 | 1.00% | -2.67% | 4.67% | 1.3077 | 0.7905 | 1.0000 |
| ml_first_two_kills_vs_existing_rule | 200 | -8.00% | -15.66% | -0.34% | 0.5949 | 0.0559 | 0.1677 |
| continuous_frozen_ml_vs_existing_rule | 200 | -10.00% | -18.45% | -1.55% | 0.5876 | 0.0286 | 0.1145 |
| selective_ml_override_vs_existing_rule | 200 | -1.00% | -2.38% | 0.38% | 0.2000 | 0.5000 | 1.0000 |

## Single-Intervention and Continuous Comparison

| Analysis | Condition | Branch | N | Wolf Win/Value | Avg Interventions | Note |
| --- | --- | --- | --- | --- | --- | --- |
| complete_game_policy | ml_first_kill_only |  | 200 | 72.00% | 1.0000 | live complete-game policy |
| complete_game_policy | ml_single_random_kill |  | 200 | 66.50% | 0.9700 | live complete-game policy |
| complete_game_policy | ml_first_two_kills |  | 200 | 63.00% | 2.0000 | live complete-game policy |
| complete_game_policy | continuous_frozen_ml |  | 200 | 61.00% | 3.3450 | live complete-game policy |
| complete_game_policy | selective_ml_override |  | 200 | 70.00% | 0.1850 | live complete-game policy |
| single_intervention_rollout |  | existing_rule_forced_once |  | 78.00% |  |  |
| single_intervention_rollout |  | frozen_ml_forced_once |  | 80.00% |  |  |
| paired_single_intervention_difference |  | frozen_ml_minus_existing_rule |  | 2.00% |  |  |

## Conclusion Label

`weak/inconclusive`

The existing rule remains the default wolf-kill policy. Selective override is
reported as a diagnostic condition, not deployed as a new default.
