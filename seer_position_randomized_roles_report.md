# Seer Position Strategy with Randomized Seat-Role Assignment Report

## 1. Purpose

The earlier seer position experiment tested whether seat-based checking strategies, such as edge-first checking, improve village outcomes in a fixed 10-player role setup. However, fixed role placement can accidentally make some position strategies look stronger or weaker because certain roles repeatedly appear in the same seats.

This follow-up experiment randomizes role assignment across seats while keeping seat numbers fixed. The goal is to test whether position-based seer checking remains useful after removing fixed seat-role structure.

## 2. Randomized Seat-Role Assignment

The randomized role assignment follows these rules:

- `player_id` remains the seat number.
- `side` and `seat_type` are determined only by `player_id`.
- Roles are shuffled across seats each game.
- The 10-player role pool is fixed:
  - 3 werewolves
  - 4 villagers
  - 1 seer
  - 1 witch
  - 1 hunter

The mechanism is controlled by `randomize_seat_roles=False` by default. Existing experiments are unchanged unless they explicitly enable the toggle.

Each randomized game logs one `seat_role_assignment` event containing the seat-role mapping and aggregate seat statistics.

## 3. Experiment Conditions

The randomized-role experiment uses the same seven seer checking strategies as the prior position experiment:

| Condition | Strategy |
|---|---|
| `seer_default` | Original seer behavior. |
| `seer_random` | Random alive non-self checking with repeat avoidance. |
| `seer_edge_first` | Prioritizes edge seats. |
| `seer_inner_first` | Prioritizes inner seats. |
| `seer_highest_p_wolf` | Checks the highest current `p_wolf` target. |
| `seer_highest_suspicion` | Checks the highest current `suspicion_score` target. |
| `seer_opposite_side` | Prioritizes the side opposite the seer. |

The base environment uses the existing 10-player setup with speech, deception credibility costs, speaker memory, and position model enabled. Limited last words and risk preference are disabled.

## 4. Single-Seed Results

The single-seed experiment uses 500 games with seed 42.

| Condition | Wolf win rate | Village win rate | Seer found wolf rate | First check found wolf rate | Edge check rate | Avg wolves on edge |
|---|---:|---:|---:|---:|---:|---:|
| `seer_default` | 62.60% | 37.40% | 30.80% | 34.20% | 40.42% | 1.22 |
| `seer_random` | 61.60% | 38.40% | 34.32% | 31.20% | 41.09% | 1.17 |
| `seer_edge_first` | 60.80% | 39.20% | 34.30% | 31.20% | 88.82% | 1.15 |
| `seer_inner_first` | 56.00% | 44.00% | 36.03% | 32.00% | 3.70% | 1.22 |
| `seer_highest_p_wolf` | 63.00% | 37.00% | 34.92% | 33.40% | 41.40% | 1.21 |
| `seer_highest_suspicion` | 65.60% | 34.40% | 36.13% | 32.00% | 42.61% | 1.23 |
| `seer_opposite_side` | 57.80% | 42.20% | 36.10% | 31.80% | 40.44% | 1.14 |

With randomized seat-role assignment, no strategy reaches the village win rates seen in the fixed-role seer position experiment. The best single-seed village result is `seer_inner_first` at 44.00%, followed by `seer_opposite_side` at 42.20%.

## 5. Multi-Seed Robustness

The multi-seed experiment uses seeds 42, 43, 44, 45, and 46, with 500 games per condition per seed.

| Condition | Wolf mean | Wolf min | Wolf max | Wolf stdev pp | Village mean | Seer found wolf rate mean | First check found wolf rate mean | Edge check rate mean | Avg wolves on edge mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `seer_default` | 62.52 | 60.60 | 64.00 | 1.24 | 37.48 | 32.10 | 33.44 | 41.63 | 1.20 |
| `seer_random` | 59.48 | 57.00 | 61.60 | 2.04 | 40.52 | 35.48 | 34.72 | 41.83 | 1.20 |
| `seer_edge_first` | 58.56 | 54.60 | 60.80 | 2.51 | 41.44 | 36.84 | 34.20 | 88.90 | 1.22 |
| `seer_inner_first` | 58.32 | 55.80 | 62.60 | 2.76 | 41.68 | 35.02 | 31.80 | 3.59 | 1.22 |
| `seer_highest_p_wolf` | 65.12 | 63.00 | 67.40 | 1.99 | 34.88 | 34.63 | 32.44 | 41.92 | 1.21 |
| `seer_highest_suspicion` | 65.16 | 63.60 | 66.00 | 0.92 | 34.84 | 35.21 | 33.56 | 42.36 | 1.22 |
| `seer_opposite_side` | 60.48 | 57.80 | 62.60 | 1.90 | 39.52 | 35.94 | 32.00 | 40.01 | 1.20 |

The multi-seed results show that `seer_inner_first` and `seer_edge_first` are the strongest village strategies under randomized role assignment, but the differences are modest. `seer_inner_first` has the lowest wolf mean at 58.32%, while `seer_edge_first` is close at 58.56%.

## 6. Interpretation

Randomizing roles across seats substantially weakens the earlier fixed-seat conclusions. In the fixed-role experiment, some strategies benefited or suffered from the fact that wolves and the seer repeatedly occupied the same seats. After randomization, edge-first no longer has a clear structural advantage.

`seer_edge_first` still performs slightly better than `seer_default`, but it is not decisively better than `seer_inner_first`. Its wolf discovery rate mean is 36.84%, compared with 35.02% for `seer_inner_first`, but its village mean is slightly lower at 41.44% versus 41.68%.

The behavioral strategies, `highest_p_wolf` and `highest_suspicion`, perform worse under randomized role assignment in this environment. This suggests that early behavioral risk scores may be noisier when role location is randomized, especially because the seer can no longer exploit fixed role-position structure.

Overall, seat position appears to be a weak heuristic rather than a robust rule. It may help organize checking behavior, but it should not be treated as evidence by itself.

## 7. Seat Distribution Diagnostics

The randomized assignment produced stable seat-role distribution statistics. Across the multi-seed conditions, edge seats had at least one wolf in roughly 82.68%-84.44% of games, and the average number of wolves on edge seats was about 1.20-1.22.

This confirms that the randomization is active and that edge seats often contain wolves simply because there are four edge seats and three wolves. However, edge presence alone does not translate into a decisive village advantage.

## 8. Financial Analogy

Randomized seat-role assignment is similar to stress-testing a risk model under shuffled network positions. If a strategy works only when risky actors occupy fixed locations, it may be overfitting to structure rather than learning robust signals.

Edge seats resemble boundary nodes in a network. Auditing boundary nodes can be useful, but this experiment shows that structural position should be validated against randomized baselines. In risk management terms, seat position is a prior, not proof.

## 9. Limitations

This experiment remains intentionally limited:

- The seat model is still a simple left/right split.
- Seat position does not affect speech order, voting attention, or herding.
- Roles are randomized uniformly rather than using human-like seat selection.
- Only seer checking strategy is varied.
- No payoff rules, role abilities, or language mechanisms were changed.

## 10. Conclusion

The randomized seat-role assignment experiment suggests that edge-first checking is not a stable universal rule. It performs better than default checking, but it does not clearly dominate inner-first checking. The earlier position results were partly dependent on fixed role-seat structure.

The strongest conclusion is methodological: position logic should be evaluated against randomized baselines before being interpreted as strategic evidence.
