# Structured Seer Search Experiment Report

## Overview

This experiment compares random, positional, behavioral, and structured sequential seer search strategies in the existing 10-player randomized-role Werewolf simulation. Game rules, role composition, speech, voting, night actions, and payoff rules are unchanged from the previous randomized-role seer-position setup.

## Design

- Strategies: 14
- Seeds: 42, 43, 44, 45, 46
- Games per strategy per seed: 500
- Total games: 35000
- Seat-role assignment: randomized each game
- Repeat check guard: enabled for this experiment only

## Strategy Definitions

- `random`: Randomly chooses among alive, unchecked, non-self targets.
- `default`: Uses the existing default random seer strategy, with the structured experiment repeat guard enabled.
- `edge_first`: Uses the existing edge-first positional strategy.
- `inner_first`: Uses the existing inner-first positional strategy.
- `highest_p_wolf`: Checks the alive unchecked player with the highest current p_wolf.
- `highest_suspicion`: Checks the alive unchecked player with the highest suspicion_score.
- `left_to_right`: Checks alive unchecked targets in increasing seat-number order.
- `right_to_left`: Checks alive unchecked targets in decreasing seat-number order.
- `alternate_sides`: Alternates between the side opposite the seer and the seer's own side. Ties are broken by nearest circular distance, then lower seat.
- `nearest_first`: Checks the alive unchecked target with minimum circular distance from the seer's seat.
- `farthest_first`: Checks the alive unchecked target with maximum circular distance from the seer's seat.
- `coverage_balanced`: Chooses the unchecked target that maximizes distance from already checked seats, then distance from the seer, then lower seat.
- `hybrid_suspicion_position`: Scores targets as suspicion_score + 0.25 * coverage_bonus.
- `information_gain_proxy`: Uses a visible-information proxy: 0.35 * unseen-side bonus + 0.25 * unseen-seat-type bonus + 0.25 * normalized distance + 0.15 * average(p_wolf, suspicion_score).

## Descriptive Strategy Summary

| strategy | village win | wolf win | first check wolf | found by check 2 | found by check 3 | mean checks until first wolf | no wolf found | wolves found/game | seer survival | mean checks | coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 40.52% | 59.48% | 34.72% | 54.68% | 63.60% | 1.69 | 33.76% | 0.94 | 30.32% | 2.64 | 0.29 |
| default | 40.52% | 59.48% | 34.72% | 54.68% | 63.60% | 1.69 | 33.76% | 0.94 | 30.32% | 2.64 | 0.29 |
| edge_first | 41.44% | 58.56% | 34.20% | 56.60% | 65.76% | 1.70 | 32.04% | 0.96 | 30.80% | 2.61 | 0.29 |
| inner_first | 42.08% | 57.92% | 31.48% | 54.32% | 63.00% | 1.74 | 34.24% | 0.92 | 31.44% | 2.63 | 0.29 |
| highest_p_wolf | 34.88% | 65.12% | 32.44% | 53.52% | 63.12% | 1.71 | 34.96% | 0.91 | 28.84% | 2.63 | 0.29 |
| highest_suspicion | 34.84% | 65.16% | 33.56% | 53.76% | 62.28% | 1.68 | 35.40% | 0.91 | 26.12% | 2.59 | 0.29 |
| left_to_right | 40.84% | 59.16% | 33.72% | 54.76% | 63.44% | 1.71 | 33.60% | 0.94 | 31.00% | 2.62 | 0.29 |
| right_to_left | 43.88% | 56.12% | 33.28% | 54.56% | 64.36% | 1.72 | 33.28% | 0.97 | 33.68% | 2.66 | 0.30 |
| alternate_sides | 44.16% | 55.84% | 33.24% | 55.04% | 63.28% | 1.72 | 33.40% | 0.94 | 31.72% | 2.64 | 0.29 |
| nearest_first | 41.68% | 58.32% | 33.16% | 55.56% | 64.60% | 1.72 | 32.80% | 0.96 | 31.48% | 2.66 | 0.30 |
| farthest_first | 42.88% | 57.12% | 32.20% | 54.04% | 62.80% | 1.73 | 34.28% | 0.93 | 31.32% | 2.61 | 0.29 |
| coverage_balanced | 41.28% | 58.72% | 33.92% | 55.60% | 64.68% | 1.69 | 33.12% | 0.95 | 30.60% | 2.63 | 0.29 |
| hybrid_suspicion_position | 36.84% | 63.16% | 32.88% | 55.12% | 63.72% | 1.70 | 33.92% | 0.94 | 29.88% | 2.60 | 0.29 |
| information_gain_proxy | 41.12% | 58.88% | 33.60% | 55.56% | 64.64% | 1.72 | 32.68% | 0.96 | 31.56% | 2.61 | 0.29 |

## Validation

- Row count: 35000
- Unique game ids: True
- Validation passed: True
- No invalid winners, duplicate game ids, duplicate seer check targets, self-checks, distance errors, or row-count mismatches were detected.

## Notes

This report contains descriptive results only. Formal hypothesis tests, confidence intervals, and effect-size estimation are intentionally deferred to the next Data Analytics stage.

Runtime: 44.27 seconds.
