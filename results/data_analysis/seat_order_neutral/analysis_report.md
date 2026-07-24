# Seat-Order-Neutral Directional Effects Analysis

## Technical Summary

This analysis uses the seat-order-neutral game-level dataset and collapses the normal, mirrored, and rotated label rows to one independent row per strategy/base configuration before estimating strategy effects. The source file has 30,000 completed games, but the effective independent sample for strategy inference is 10,000 strategy/base rows, with 2,500 shared physical configurations available for paired cross-strategy comparisons.

Validation status: passed. Displayed-label invariance is exactly observed across normal, mirrored, and rotated labels.

Descriptively, `physical_clockwise` has a village win rate of 43.24%, above `physical_counterclockwise` at 40.72% and `random_neutral` at 40.20%. The seed-adjusted model and paired analysis show positive clockwise differences over counterclockwise and random, but these differences remain statistically uncertain after multiple comparison correction and do not support clockwise as better than alternate physical sides.

## Data Validation and Label Invariance

| validation check | observed | expected | passed |
|---|---:|---:|---|
| row_count | 30000 | 30000 | True |
| unique_matched_sets | 10000 | 10000 | True |
| three_label_rows_per_matched_set | 10000 | 10000 | True |
| four_strategies | alternate_physical_sides,physical_clockwise,physical_counterclockwise,random_neutral | alternate_physical_sides,physical_clockwise,physical_counterclockwise,random_neutral | True |
| seeds_42_to_46 | 42,43,44,45,46 | 42,43,44,45,46 | True |
| 500_base_configs_per_strategy_seed | 20 | 20 | True |
| valid_winners | village,wolf | draw,village,wolf subset | True |
| unique_game_ids | 30000 | 30000 | True |
| no_duplicate_seer_checks | 0 | 0 | True |
| physical_seer_seat_identical_across_label_conditions | 10000 | 10000 | True |
| physical_wolf_seats_identical_across_label_conditions | 10000 | 10000 | True |
| all_check_physical_targets_identical_across_label_conditions | 10000 | 10000 | True |
| winner_identical_across_label_conditions | 10000 | 10000 | True |
| total_rounds_identical_across_label_conditions | 10000 | 10000 | True |
| seer_survived_to_game_end_identical_across_label_conditions | 10000 | 10000 | True |
| physical_check_sequence_flag_matches_reference | 20000 | 20000 | True |
| winner_flag_matches_reference | 20000 | 20000 | True |
| final_physical_alive_set_matches_reference | 20000 | 20000 | True |
| no_recorded_divergence | none | none | True |
| neutral_mode_enabled_all_rows | 30000 | 30000 | True |
| physical_outcome_mechanism_duplicates_identical | 0 | 0 | True |

The three label conditions are deterministic physical duplicates for the outcome and mechanism fields tested. This should be read as computational equivalence, not merely failure to reject a label effect.

## Descriptive Statistics

| strategy | independent games | village win | 95% CI | wolf win | first check wolf | found by check 2 | found by check 3 | no wolf found | mean checks to first wolf | seer survival | mean rounds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| physical_clockwise | 2500 | 43.24% | 41.31%-45.19% | 56.76% | 32.80% | 55.44% | 64.08% | 33.24% | 1.72 | 29.68% | 3.40 |
| physical_counterclockwise | 2500 | 40.72% | 38.81%-42.66% | 59.28% | 33.72% | 55.72% | 63.80% | 34.08% | 1.68 | 30.48% | 3.40 |
| alternate_physical_sides | 2500 | 42.52% | 40.59%-44.47% | 57.48% | 32.80% | 55.00% | 64.32% | 33.20% | 1.72 | 30.84% | 3.40 |
| random_neutral | 2500 | 40.20% | 38.29%-42.14% | 59.80% | 35.04% | 55.56% | 63.56% | 33.72% | 1.67 | 30.60% | 3.42 |

## Primary Strategy Model

The seed-adjusted logistic model `village_win ~ strategy + seed` finds an overall strategy effect (LR=6.43, df=3, p=0.0925).

| contrast | adjusted OR | 95% CI | adjusted probability difference | raw p | Holm p | interpretation |
|---|---:|---:|---:|---:|---:|---|
| physical_clockwise vs physical_counterclockwise | 1.109 | 0.991-1.241 | 2.52 pp | 0.0710 | 0.3552 | practically meaningful but statistically uncertain |
| physical_clockwise vs random_neutral | 1.133 | 1.013-1.268 | 3.04 pp | 0.0293 | 0.1758 | practically meaningful but statistically uncertain |
| physical_clockwise vs alternate_physical_sides | 1.030 | 0.921-1.152 | 0.72 pp | 0.6070 | 1.0000 | unsupported |
| alternate_physical_sides vs random_neutral | 1.100 | 0.983-1.232 | 2.32 pp | 0.0958 | 0.3832 | practically meaningful but statistically uncertain |
| physical_counterclockwise vs random_neutral | 1.022 | 0.913-1.144 | 0.52 pp | 0.7080 | 1.0000 | unsupported |
| alternate_physical_sides vs physical_counterclockwise | 1.077 | 0.962-1.205 | 1.80 pp | 0.1967 | 0.5900 | unsupported |

## Paired Configuration Analysis

Cross-strategy pairing is valid: the same `seed` and `base_game_index` reuse the same physical seer seat and physical wolf seats across all four strategies. The paired analysis uses 2,500 shared physical configurations and is preferred for strategy comparisons because it removes role-layout noise.

| contrast | paired diff | 95% CI | discordant A win/B win | paired OR | raw p | Holm p | interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| physical_clockwise vs physical_counterclockwise | 2.52 pp | -0.01 pp-5.05 pp | 551/488 | 1.129 | 0.0544 | 0.2718 | practically meaningful but statistically uncertain |
| physical_clockwise vs random_neutral | 3.04 pp | 0.66 pp-5.42 pp | 500/424 | 1.179 | 0.0136 | 0.0814 | practically meaningful but statistically uncertain |
| physical_clockwise vs alternate_physical_sides | 0.72 pp | -1.34 pp-2.78 pp | 353/335 | 1.054 | 0.5169 | 1.0000 | unsupported |
| alternate_physical_sides vs random_neutral | 2.32 pp | -0.12 pp-4.76 pp | 512/454 | 1.128 | 0.0666 | 0.2718 | practically meaningful but statistically uncertain |
| physical_counterclockwise vs random_neutral | 0.52 pp | -1.89 pp-2.93 pp | 478/465 | 1.028 | 0.6960 | 1.0000 | unsupported |
| alternate_physical_sides vs physical_counterclockwise | 1.80 pp | -0.65 pp-4.25 pp | 511/466 | 1.097 | 0.1592 | 0.4776 | unsupported |

## Early Discovery and Mechanisms

`physical_clockwise` wins more often than `random_neutral` even though its first-check wolf rate is lower (32.80% vs 35.04%). The gap is not explained by first-check success alone. Clockwise has slightly better discovery by check 3 and a slightly lower no-wolf-found rate than random, but the mechanism models show the clockwise coefficient remains materially positive after adding early-discovery, timing, survival, and game-length diagnostics. These variables are intermediate/post-treatment, so the models are diagnostic rather than causal mediation.

| model | converged | cw vs random OR | cw vs random p | cw vs counter OR | cw vs counter p | cw-random adjusted pp | note |
|---|---:|---:|---:|---:|---:|---:|---|
| A_strategy_seed | True | 1.133 | 0.0293 | 1.109 | 0.0710 | 3.04 | diagnostic only; added terms may be intermediate/post-treatment |
| B_plus_first_check_wolf | True | 1.147 | 0.0176 | 1.115 | 0.0586 | 3.29 | diagnostic only; added terms may be intermediate/post-treatment |
| C_plus_check2_check3 | True | 1.132 | 0.0348 | 1.109 | 0.0770 | 2.88 | diagnostic only; added terms may be intermediate/post-treatment |
| D_plus_timing_no_wolf | True | 1.130 | 0.0384 | 1.101 | 0.1035 | 2.81 | diagnostic only; added terms may be intermediate/post-treatment |
| E_plus_seer_survival | True | 1.177 | 0.0084 | 1.145 | 0.0282 | 3.41 | diagnostic only; added terms may be intermediate/post-treatment |
| F_plus_checks_rounds | True | 1.153 | 0.0193 | 1.131 | 0.0426 | 3.09 | diagnostic only; added terms may be intermediate/post-treatment |
| G_full_diagnostic | False | 1.186 | 0.0071 | 1.144 | 0.0337 | 3.41 | diagnostic only; added terms may be intermediate/post-treatment |

## Physical Layout Interactions

| variable | LR statistic | df | p-value | interpretation |
|---|---:|---:|---:|---|
| physical_seer_seat | 17.41 | 27 | 0.9204 | no strong interaction evidence |
| clockwise_wolf_count | 72.23 | 3 | 0.0000 | layout-dependent strategy performance |
| counterclockwise_wolf_count | 76.41 | 3 | 0.0000 | layout-dependent strategy performance |
| nearest_clockwise_wolf_distance | 68.33 | 3 | 0.0000 | layout-dependent strategy performance |
| nearest_counterclockwise_wolf_distance | 79.53 | 3 | 0.0000 | layout-dependent strategy performance |
| first_check_target_is_wolf | 6.18 | 3 | 0.1030 | no strong interaction evidence |
| wolves_on_edge | 7.28 | 3 | 0.0636 | no strong interaction evidence |
| local_wolf_density_near_seer | 22.00 | 3 | 0.0001 | layout-dependent strategy performance |
| layout_condition | 78.55 | 6 | 0.0000 | layout-dependent strategy performance |

The interaction checks suggest that strategy performance is partly conditional on physical wolf layout and local wolf density. The seer-seat interaction itself is not strong in this diagnostic model. Overall, this supports a path-layout interpretation over a pure displayed-label artifact.

## Seed Robustness

| seed | physical_clockwise | physical_counterclockwise | alternate_physical_sides | random_neutral |
|---:|---:|---:|---:|---:|
| 42 | 41.20% | 39.60% | 39.40% | 43.40% |
| 43 | 44.80% | 41.20% | 43.40% | 39.80% |
| 44 | 44.60% | 41.40% | 43.60% | 40.20% |
| 45 | 44.20% | 41.00% | 43.80% | 38.20% |
| 46 | 41.40% | 40.40% | 42.40% | 39.40% |

Only five seeds are available, so the robustness section relies on seed fixed effects, seed-stratified rates, leave-one-seed-out models, and paired configuration tests rather than cluster-robust standard errors.

## Answers to Required Questions

1. **Is physical_clockwise statistically better than physical_counterclockwise?** practically meaningful but statistically uncertain. Seed-adjusted Holm p=0.3552; paired Holm p=0.2718.
2. **Is physical_clockwise statistically better than random_neutral?** practically meaningful but statistically uncertain. Seed-adjusted Holm p=0.1758; paired Holm p=0.0814.
3. **Is alternate_physical_sides statistically better than random_neutral?** practically meaningful but statistically uncertain. Seed-adjusted Holm p=0.3832; paired Holm p=0.2718.
4. **Did displayed-label condition have exactly zero physical effect?** statistically supported as deterministic equivalence. All tested physical trajectories and outcomes match exactly across label conditions.
5. **Is the clockwise advantage stable across seeds?** practically meaningful but statistically uncertain. Clockwise beats counterclockwise in most seed-level cuts, but five seeds are too few for a final robustness claim by seed alone.
6. **Does the clockwise advantage survive paired configuration analysis?** practically meaningful but statistically uncertain. Paired difference=2.52 pp.
7. **Why does clockwise win more despite a lower first-check wolf rate than random?** weak/inconclusive mechanism. The gain is not a first-check story; later discovery and path composition appear more relevant, but the staged models are diagnostic only.
8. **Is the advantage explained by later discovery or seer survival?** weak/inconclusive. Adjustment does not eliminate the clockwise coefficient, so no single measured downstream mechanism fully explains it.
9. **Does the advantage depend on where wolves are physically located?** practically meaningful but statistically uncertain. Layout interaction checks show dependence on wolf placement and local wolf density, consistent with path-layout alignment.
10. **Is this a real directional search effect or favorable path alignment?** weak/inconclusive. The result is label-invariant, but path-layout alignment and residual physical-engine asymmetry remain possible explanations.
11. **Are residual engine asymmetries still possible?** yes. A full supplied-action replay harness was not implemented, so the final physical-direction claim remains limited.
12. **Is the structured-search chapter ready to close?** not fully. Displayed-label artifacts are controlled, but physical direction needs a stronger engine-symmetry validation.
13. **What exact experiment should come next?** next step. Build a full supplied-action replay or randomized physical-orientation experiment that swaps clockwise/counterclockwise geometry while preserving action traces.

## Output Files

- `results/data_analysis/seat_order_neutral/validation_summary.csv`
- `results/data_analysis/seat_order_neutral/descriptive_statistics.csv`
- `results/data_analysis/seat_order_neutral/strategy_omnibus_tests.csv`
- `results/data_analysis/seat_order_neutral/primary_pairwise_contrasts.csv`
- `results/data_analysis/seat_order_neutral/paired_strategy_analysis.csv`
- `results/data_analysis/seat_order_neutral/label_invariance_validation.csv`
- `results/data_analysis/seat_order_neutral/early_discovery_analysis.csv`
- `results/data_analysis/seat_order_neutral/mechanism_models.csv`
- `results/data_analysis/seat_order_neutral/physical_layout_interactions.csv`
- `results/data_analysis/seat_order_neutral/seed_robustness.csv`
- `results/data_analysis/seat_order_neutral/effect_size_precision.csv`
- `results/data_analysis/seat_order_neutral/residual_validity_assessment.md`
