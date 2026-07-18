# Seer Position Strategy Experiment Report

## 1. Purpose

Seat-position logic is common in Werewolf discussions, but this project does not treat it as a fixed truth. Instead, position logic is modeled as a testable hypothesis.

This experiment asks whether a seer benefits from checking players based on seat position in a 10-player Werewolf simulation. The central question is whether edge-first checking improves wolf discovery or village win rate compared with random checking, inner-first checking, behavioral risk-score checking, or opposite-side checking.

## 2. Position Model

The first position model uses a simple 10-player table structure:

- Left side: seats 1, 2, 3, 4, 5
- Right side: seats 6, 7, 8, 9, 10
- Edge seats: 1, 5, 6, 10
- Inner seats: 2, 3, 4, 7, 8, 9

This structure is intentionally minimal. Position affects only the seer's checking strategy in this experiment. It does not affect speech order, voting order, attention, herding, or payoff rules.

## 3. Hypotheses

H1: Edge-first seer checking may improve information discovery.

H2: Edge seats are not guaranteed to contain wolves, but may have structural value.

H3: Opposite-side checking may reveal cross-side structure.

H4: Suspicion-based checking may outperform position-only checking if behavioral signals are informative.

## 4. Experiment Conditions

The experiment compares seven seer checking strategies:

| Condition | Strategy |
|---|---|
| `seer_default` | Original seer behavior. |
| `seer_random` | Randomly checks an alive non-self player while avoiding repeat checks when possible. |
| `seer_edge_first` | Prioritizes edge seats: 1, 5, 6, 10. |
| `seer_inner_first` | Prioritizes inner seats: 2, 3, 4, 7, 8, 9. |
| `seer_highest_p_wolf` | Checks the alive non-self player with the highest current `p_wolf`. |
| `seer_highest_suspicion` | Checks the alive non-self player with the highest current `suspicion_score`. |
| `seer_opposite_side` | Prioritizes players on the opposite side of the table. |

The base environment uses the existing 10-player role setup with speech, deception credibility costs, and speaker memory enabled. Limited last words and risk preference are disabled to avoid mixing this experiment with later-stage mechanisms.

## 5. Main Results

The single-seed experiment uses 500 games with seed 42.

| Condition | Wolf win rate | Village win rate | Seer found wolf rate | First check found wolf rate | Edge checks | Inner checks |
|---|---:|---:|---:|---:|---:|---:|
| `seer_default` | 43.00% | 57.00% | 27.40% | 31.80% | 649 | 749 |
| `seer_random` | 32.80% | 67.20% | 36.85% | 36.40% | 634 | 742 |
| `seer_edge_first` | 34.80% | 65.20% | 30.45% | 24.00% | 1305 | 117 |
| `seer_inner_first` | 36.80% | 63.20% | 38.67% | 41.80% | 97 | 1302 |
| `seer_highest_p_wolf` | 32.40% | 67.60% | 40.90% | 28.40% | 636 | 677 |
| `seer_highest_suspicion` | 38.80% | 61.20% | 37.94% | 32.60% | 599 | 719 |
| `seer_opposite_side` | 46.20% | 53.80% | 7.39% | 0.00% | 635 | 881 |

In the single-seed result, `seer_highest_p_wolf` produces the strongest village win rate at 67.60%, followed closely by `seer_random` at 67.20%. `seer_edge_first` improves village win rate compared with `seer_default`, but it does not produce the highest wolf discovery rate. `seer_inner_first` finds wolves more efficiently than `seer_edge_first` in this setup.

## 6. Multi-Seed Robustness

The multi-seed experiment uses seeds 42, 43, 44, 45, and 46, with 500 games per condition per seed.

| Condition | Wolf mean | Wolf min | Wolf max | Wolf stdev pp | Village mean | Seer found wolf rate mean | First check found wolf rate mean | Edge check rate mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `seer_default` | 43.08 | 41.20 | 45.60 | 1.68 | 56.92 | 29.20 | 34.28 | 47.31 |
| `seer_random` | 33.96 | 32.80 | 36.20 | 1.32 | 66.04 | 35.55 | 34.12 | 46.43 |
| `seer_edge_first` | 37.20 | 33.80 | 41.40 | 3.60 | 62.80 | 30.31 | 24.44 | 90.82 |
| `seer_inner_first` | 36.48 | 35.20 | 39.00 | 1.57 | 63.52 | 38.68 | 40.52 | 6.80 |
| `seer_highest_p_wolf` | 32.60 | 28.00 | 35.00 | 2.73 | 67.40 | 41.92 | 33.52 | 47.49 |
| `seer_highest_suspicion` | 37.60 | 35.60 | 39.00 | 1.38 | 62.40 | 39.57 | 33.92 | 45.60 |
| `seer_opposite_side` | 46.44 | 45.60 | 48.40 | 1.15 | 53.56 | 6.76 | 0.00 | 42.20 |

The multi-seed results support the single-seed pattern. `seer_highest_p_wolf` has the lowest wolf mean at 32.60% and the highest village mean at 67.40%. `seer_random` is close behind with a 33.96% wolf mean and 66.04% village mean.

`seer_edge_first` does improve over `seer_default`, reducing wolf mean from 43.08% to 37.20%. However, it does not outperform `seer_random`, `seer_inner_first`, or `seer_highest_p_wolf`. Its seer found wolf rate mean is 30.31%, only slightly above the default value of 29.20%.

`seer_inner_first` performs better than `seer_edge_first` on wolf discovery, with a seer found wolf rate mean of 38.68% and a first-check found wolf rate mean of 40.52%. This is likely connected to the current role setup, where several wolves begin in low-number inner/near-inner positions. This means position results should be interpreted as configuration-dependent rather than universal.

`seer_opposite_side` performs worst in this setup. Its first-check found wolf rate mean is 0.00%, and its seer found wolf rate mean is only 6.76%. This is because the current 10-player role setup places the seer on the left side and all wolves on the left side, so opposite-side checking systematically checks away from wolves early.

## 7. Interpretation

Edge-first checking is partially supported but not strongly supported. It improves village win rate relative to the default strategy, but it does not produce the best village win rate or the best wolf discovery rate.

The strongest overall strategy is `highest_p_wolf`, which suggests that behavioral belief scores are more useful than seat position alone when the simulation has speech and belief updates. `highest_suspicion` also performs competitively, though not as strongly as `highest_p_wolf`.

Position logic is useful as a controlled comparison, but it should not replace behavioral evidence. In this experiment, inner-first checking and p-wolf-based checking outperform edge-first checking on wolf discovery. Opposite-side checking demonstrates the risk of applying structural heuristics without validating them against the actual role distribution.

## 8. Financial Analogy

Seat position is similar to structural market position or network location. Edge seats resemble actors at the boundary of information clusters, while inner seats resemble actors embedded inside local clusters.

Checking edge seats is analogous to auditing boundary nodes in a network, such as counterparties that connect separate trading groups or operational units. This can be useful, but structural location alone should not replace behavioral evidence. The strongest result in this experiment comes from `p_wolf`, which is closer to a dynamic risk score built from observed signals.

The broader lesson is that network position may guide attention, but risk scoring should combine structure with behavior.

## 9. Limitations

This experiment has several important limitations:

- The left/right position model is simple and fixed.
- There is no real human seating behavior.
- Seat position does not affect speech order.
- Seat position does not affect vote attention or herding pressure.
- Only seer checking strategy is tested in this stage.
- The current 10-player role setup places wolves in specific seats, so results may depend on the role assignment pattern.
- The model does not yet randomize seat-role assignment across games.

## 10. Conclusion

The experiment does not support treating edge-first checking as a universal rule. Edge-first checking improves over the default seer behavior, but it is not the best strategy in either the single-seed or multi-seed results. Behavioral strategies, especially `highest_p_wolf`, are more effective in this setup.

Position-based reasoning remains useful as a testable heuristic, but it should be evaluated empirically and combined with behavioral risk signals rather than treated as fixed Werewolf theory.
