# Seat-Order-Neutral Directional Replication Report

## Overview

This experiment adds an explicit seat-order-neutral engine mode and repeats the directional seer-search comparison with physical direction strategies. The default simulator behavior is not changed; neutralization is enabled only through `seat_order_neutral_mode=True`.

## Neutralization Rules

- Stable `actor_uid` is the physical actor identity.
- `physical_seat` is the circular layout position.
- `displayed_player_id` is the visible numeric label.
- Roles are assigned to physical seats before label mapping.
- Speech and voting iterate through a neutral actor order.
- Speech RNG uses actor_uid-based sha256 sub-seeds.
- Exact ties use displayed-label-independent actor tie-breaks.

## Experiment Scale

- Seeds: 42, 43, 44, 45, 46
- Base configurations per strategy-seed: 500
- Strategies: physical_clockwise, physical_counterclockwise, alternate_physical_sides, random_neutral
- Label conditions: normal, mirrored, rotated
- Matched sets: 10000
- Completed games: 30000

## Strategy by Label Condition

| strategy | label | games | village win | wolf win | first check wolf | found by check 2 | found by check 3 | seer survival | mean checks | paired outcome agreement |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| alternate_physical_sides | mirrored | 2500 | 42.52% | 57.48% | 32.80% | 55.00% | 64.32% | 30.84% | 2.60 | 100.00% |
| alternate_physical_sides | normal | 2500 | 42.52% | 57.48% | 32.80% | 55.00% | 64.32% | 30.84% | 2.60 | NA |
| alternate_physical_sides | rotated | 2500 | 42.52% | 57.48% | 32.80% | 55.00% | 64.32% | 30.84% | 2.60 | 100.00% |
| physical_clockwise | mirrored | 2500 | 43.24% | 56.76% | 32.80% | 55.44% | 64.08% | 29.68% | 2.60 | 100.00% |
| physical_clockwise | normal | 2500 | 43.24% | 56.76% | 32.80% | 55.44% | 64.08% | 29.68% | 2.60 | NA |
| physical_clockwise | rotated | 2500 | 43.24% | 56.76% | 32.80% | 55.44% | 64.08% | 29.68% | 2.60 | 100.00% |
| physical_counterclockwise | mirrored | 2500 | 40.72% | 59.28% | 33.72% | 55.72% | 63.80% | 30.48% | 2.60 | 100.00% |
| physical_counterclockwise | normal | 2500 | 40.72% | 59.28% | 33.72% | 55.72% | 63.80% | 30.48% | 2.60 | NA |
| physical_counterclockwise | rotated | 2500 | 40.72% | 59.28% | 33.72% | 55.72% | 63.80% | 30.48% | 2.60 | 100.00% |
| random_neutral | mirrored | 2500 | 40.20% | 59.80% | 35.04% | 55.56% | 63.56% | 30.60% | 2.61 | 100.00% |
| random_neutral | normal | 2500 | 40.20% | 59.80% | 35.04% | 55.56% | 63.56% | 30.60% | 2.61 | NA |
| random_neutral | rotated | 2500 | 40.20% | 59.80% | 35.04% | 55.56% | 63.56% | 30.60% | 2.61 | 100.00% |

## Label Condition Summary

| label | games | village win | wolf win | first check wolf | paired outcome agreement | final alive set match |
|---|---:|---:|---:|---:|---:|---:|
| mirrored | 10000 | 41.67% | 58.33% | 33.59% | 100.00% | 100.00% |
| normal | 10000 | 41.67% | 58.33% | 33.59% | NA | NA |
| rotated | 10000 | 41.67% | 58.33% | 33.59% | 100.00% | 100.00% |

## Divergence Summary

| strategy | label | first divergence phase | event type | games | share |
|---|---|---|---|---:|---:|
| alternate_physical_sides | mirrored | none | none | 2500 | 100.00% |
| alternate_physical_sides | rotated | none | none | 2500 | 100.00% |
| physical_clockwise | mirrored | none | none | 2500 | 100.00% |
| physical_clockwise | rotated | none | none | 2500 | 100.00% |
| physical_counterclockwise | mirrored | none | none | 2500 | 100.00% |
| physical_counterclockwise | rotated | none | none | 2500 | 100.00% |
| random_neutral | mirrored | none | none | 2500 | 100.00% |
| random_neutral | rotated | none | none | 2500 | 100.00% |

## Control Checks

- `random_neutral` is label-invariant: first physical targets match the normal-label reference in mirrored and rotated runs.
- A narrow no-strategy engine pair control is covered by `test_no_strategy_engine_pair_control_equivalence`, which disables seer, speech, witch, hunter, suspicion update, role prior, herding, wolf strategy, wolf deception, and speaker memory, then verifies matching winners and final physical alive sets under normal and mirrored labels.

## Pre-Specified Questions

1. Neutral mode removes lower-ID tie-breaking by using actor_uid/hash tie-breaks.
2. Speech and voting order use neutral actor order, not displayed labels.
3. Speech RNG is decoupled from displayed labels in neutral mode.
4. Normal and mirrored games share physical roles, actor order, and sub-seeds; later divergence is logged.
5. Random-neutral first-target physical agreement against normal labels averaged 100.00% across non-normal label conditions.
6. First-divergence distributions are reported in `seat_order_neutral_divergence_summary.csv`.
7. Physical clockwise and counterclockwise results are descriptive only; formal inference is deferred.
8. Stability across label conditions should be checked from the strategy summary before any directional claim.
9. The old `right_to_left` label advantage is not directly reused; direction is redefined physically.
10. Remaining label or engine asymmetry is assessed through paired agreement and divergence fields.
11. The dataset is intended for a later formal Data Analytics stage rather than final directional inference.
12. The next analysis should model strategy, label condition, seed, and paired-set agreement.

## Validation

- Expected rows: 30000
- Observed rows: 30000
- Expected matched sets: 10000
- Observed matched sets: 10000
- Unique game IDs: True
- Validation passed: True
- No row-count, game-id, matched-set, duplicate-check, self-check, role-preservation, or winner errors were found.

Runtime: 245.68 seconds.
