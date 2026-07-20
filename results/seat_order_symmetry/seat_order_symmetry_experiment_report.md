# Seat-Order Symmetry and Mirror Validation Report

This experiment tests whether seer-position findings persist when randomized roles are held fixed at stable physical seats but displayed numeric labels are mirrored. Player IDs remain displayed seat labels; physical seats are recorded separately.

## Mirror Definition

Normal orientation maps physical seat `i` to displayed seat `i`. Mirrored orientation maps physical seat `i` to displayed seat `11 - i`, so `1<->10`, `2<->9`, `3<->8`, `4<->7`, and `5<->6`.

## Experiment Scale

- Seeds: [42, 43, 44, 45, 46]
- Base configurations per seed/strategy: 500
- Strategies: left_to_right, right_to_left, alternate_sides, random, nearest_first, farthest_first
- Total game rows: 30000

## Strategy and Orientation Summary

| strategy | orientation | games | wolf_win_rate | village_win_rate | avg_rounds | first_check_wolf_rate | found_wolf_by_check_2 | found_wolf_by_check_3 | seer_survival_rate | avg_seer_checks |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| alternate_sides | mirrored | 2500 | 56.72% | 43.28% | 3.43 | 34.32% | 55.72% | 64.96% | 32.28% | 2.63 |
| alternate_sides | normal | 2500 | 56.24% | 43.76% | 3.44 | 32.84% | 54.16% | 64.24% | 30.52% | 2.65 |
| farthest_first | mirrored | 2500 | 55.72% | 44.28% | 3.42 | 33.44% | 54.72% | 63.92% | 31.68% | 2.63 |
| farthest_first | normal | 2500 | 57.80% | 42.20% | 3.42 | 33.44% | 56.12% | 64.52% | 30.04% | 2.65 |
| left_to_right | mirrored | 2500 | 57.72% | 42.28% | 3.43 | 33.20% | 55.28% | 64.52% | 30.84% | 2.63 |
| left_to_right | normal | 2500 | 57.52% | 42.48% | 3.42 | 34.00% | 55.88% | 64.56% | 33.04% | 2.65 |
| nearest_first | mirrored | 2500 | 58.80% | 41.20% | 3.41 | 33.32% | 55.28% | 64.56% | 31.72% | 2.62 |
| nearest_first | normal | 2500 | 57.84% | 42.16% | 3.40 | 32.56% | 55.12% | 64.28% | 31.44% | 2.61 |
| random | mirrored | 2500 | 57.16% | 42.84% | 3.41 | 32.80% | 53.88% | 63.44% | 30.20% | 2.62 |
| random | normal | 2500 | 57.92% | 42.08% | 3.41 | 34.40% | 56.12% | 65.48% | 32.48% | 2.63 |
| right_to_left | mirrored | 2500 | 56.28% | 43.72% | 3.44 | 34.00% | 55.24% | 64.60% | 32.16% | 2.65 |
| right_to_left | normal | 2500 | 56.68% | 43.32% | 3.42 | 33.20% | 55.72% | 65.20% | 29.60% | 2.60 |

## Seat-Role Randomization Checks

| strategy | orientation | edge_has_wolf_rate | avg_wolves_on_edge | avg_wolves_on_inner | avg_wolves_left_side | avg_wolves_right_side | seer_on_edge_rate | seer_left_side_rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| alternate_sides | mirrored | 82.32% | 1.19 | 1.81 | 1.51 | 1.49 | 41.36% | 49.92% |
| alternate_sides | normal | 82.32% | 1.19 | 1.81 | 1.49 | 1.51 | 41.36% | 50.08% |
| farthest_first | mirrored | 82.32% | 1.19 | 1.81 | 1.51 | 1.49 | 41.36% | 49.92% |
| farthest_first | normal | 82.32% | 1.19 | 1.81 | 1.49 | 1.51 | 41.36% | 50.08% |
| left_to_right | mirrored | 82.32% | 1.19 | 1.81 | 1.51 | 1.49 | 41.36% | 49.92% |
| left_to_right | normal | 82.32% | 1.19 | 1.81 | 1.49 | 1.51 | 41.36% | 50.08% |
| nearest_first | mirrored | 82.32% | 1.19 | 1.81 | 1.51 | 1.49 | 41.36% | 49.92% |
| nearest_first | normal | 82.32% | 1.19 | 1.81 | 1.49 | 1.51 | 41.36% | 50.08% |
| random | mirrored | 82.32% | 1.19 | 1.81 | 1.51 | 1.49 | 41.36% | 49.92% |
| random | normal | 82.32% | 1.19 | 1.81 | 1.49 | 1.51 | 41.36% | 50.08% |
| right_to_left | mirrored | 82.32% | 1.19 | 1.81 | 1.51 | 1.49 | 41.36% | 49.92% |
| right_to_left | normal | 82.32% | 1.19 | 1.81 | 1.49 | 1.51 | 41.36% | 50.08% |

## Paired Normal vs Mirrored Differences

| strategy | pair_count | paired_outcome_agreement_rate | mean_paired_village_win_difference |
|---|---:|---:|---:|
| alternate_sides | 2500 | 50.24% | -0.0048 |
| farthest_first | 2500 | 52.56% | 0.0208 |
| left_to_right | 2500 | 46.44% | -0.0020 |
| nearest_first | 2500 | 52.64% | -0.0096 |
| random | 2500 | 50.52% | 0.0076 |
| right_to_left | 2500 | 49.28% | 0.0040 |

## Left-to-Right vs Right-to-Left

- normal: left_to_right village win rate 42.48% vs right_to_left 43.32% (difference -0.84 percentage points).
- mirrored: left_to_right village win rate 42.28% vs right_to_left 43.72% (difference -1.44 percentage points).

## Validation

All validation checks passed: expected row count, unique game IDs, exactly two orientation rows per pair, preserved physical seer and wolf seats within pairs, and no duplicate seer checks.

## Interpretation Notes

This report is descriptive and implementation-focused. It does not perform formal statistical inference. The paired dataset is designed for downstream analysis of whether apparent positional advantages are physical-layout effects or displayed-label/order artifacts.
